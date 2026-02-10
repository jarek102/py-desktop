import asyncio
import re
import shutil
import logging
import pathlib
from gi.repository import GObject

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BrightnessService")

class SysfsMonitor(GObject.Object):
    name = GObject.Property(type=str)
    brightness = GObject.Property(type=int)
    
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.name = f"Internal ({path.name})"
        self._max = 100
        self._update_task = None
        
        try:
            self._max = int((path / "max_brightness").read_text().strip())
            current = int((path / "brightness").read_text().strip())
            self.brightness = int((current / self._max) * 100)
        except Exception as e:
            logger.error(f"Failed to init sysfs monitor {path}: {e}")
            
        self.connect("notify::brightness", self.on_change)
        
    def on_change(self, *args):
        if self._update_task and not self._update_task.done():
            self._update_task.cancel()
        self._update_task = asyncio.create_task(self.worker())
            
    async def worker(self):
        target = self.brightness
        try:
            if shutil.which("brightnessctl"):
                proc = await asyncio.create_subprocess_exec(
                    "brightnessctl", "-d", self.path.name, "s", f"{target}%",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()
            else:
                val = int((target / 100) * self._max)
                with open(self.path / "brightness", "w") as f:
                    f.write(str(val))
        except Exception as e:
            logger.warning(f"Sysfs write failed: {e}")

class DDCMonitor(GObject.Object):
    bus_id = GObject.Property(type=str)
    name = GObject.Property(type=str)
    brightness = GObject.Property(type=int)
    
    def __init__(self, bus_id, name, current, service):
        super().__init__()
        self.bus_id = bus_id
        self.name = name
        self.service = service
        self.brightness = current
        self._update_task = None
        self.connect("notify::brightness", self.on_change)
        
    def on_change(self, *args):
        if self._update_task is None or self._update_task.done():
            self._update_task = asyncio.get_event_loop().create_task(self.worker())
            
    async def worker(self):
        while True:
            target = self.brightness
            await self.service.write_brightness(self.bus_id, target)
            if self.brightness == target:
                break

class BrightnessService(GObject.Object):
    
    brightness = GObject.Property(type=int)
    busy = GObject.Property(type=bool, default=False)
    
    initialization_task = None
    
    monitors = []
        
    def __init__(self):
        super().__init__()
        
        self.connect('notify::brightness', self.update_brightness)
        self.initialization_task = asyncio.get_event_loop().create_task(self.initialize())
        
    async def initialize(self):
        self.busy = True
        self.monitors = []
        
        try:
            # 1. Internal Displays
            bl_dir = pathlib.Path("/sys/class/backlight")
            if bl_dir.exists():
                for path in bl_dir.iterdir():
                    if (path / "brightness").exists():
                        self.monitors.append(SysfsMonitor(path))

            # 2. External Displays (DDC)
            if shutil.which("ddcutil"):
                detect = await asyncio.create_subprocess_exec(
                    "ddcutil", "--terse", "detect",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await detect.communicate()
                output = stdout.decode()
                
                if detect.returncode != 0:
                    logger.error(f"ddcutil detect failed: {stderr.decode()}")

                displays = output.split("Display ")
                
                for d in displays:
                    if not d.strip(): continue
                    
                    bus_match = re.search(r"I2C bus:\s+/dev/i2c-(\d+)", d)
                    if not bus_match: continue
                    bus_id = bus_match.group(1)
                    
                    # Match "DRM connector: card1-DP-1" (newer) or "DRM_connector: ..." (older)
                    connector_match = re.search(r"DRM[ _]connector:\s+(.*)", d, re.IGNORECASE)
                    connector = connector_match.group(1).strip() if connector_match else f"Bus {bus_id}"
                    # Clean up connector name (e.g. card1-DP-1 -> DP-1)
                    connector = re.sub(r"^card\d+-", "", connector)
                    
                    # Parse "Monitor: Mfg:Model:Serial" from terse output
                    model_match = re.search(r"Monitor:\s+[^:]+:([^:]+):", d)

                    if model_match and model_match.group(1).strip():
                        model = model_match.group(1).strip()
                        name = f"{model} ({connector})"
                    else:
                        name = f"Monitor ({connector})"
                    
                    val = await self.read_brightness(bus_id)
                    if val is None: val = 50
                    
                    self.monitors.append(DDCMonitor(bus_id, name, val, self))
            
            logger.info(f"Detected Monitors: {[m.name for m in self.monitors]}")

            if self.monitors:
                self.set_property("brightness", self.monitors[0].brightness)
            
        except Exception as e:
            logger.exception(f"Initialization error: {e}")
        finally:
            self.busy = False
        
    async def read_brightness(self, bus_id) -> int | None:
        try:
            # Short timeout for reading
            proc = await asyncio.create_subprocess_exec(
                "ddcutil", "--bus", str(bus_id), "--terse", "getvcp", "10",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=2.0)
            
            # Format: "VCP 10 C <current> <max>"
            regex = r"VCP 10 C (\d+)"
            match = re.search(regex, stdout.decode())
            if match:
                return int(match.group(1))
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout reading brightness from bus {bus_id}")
            try: proc.kill()
            except: pass
        except Exception as e:
            logger.warning(f"Error reading bus {bus_id}: {e}")
        return None
    
    async def write_brightness(self, bus_id, target_brightness) -> None:
        # RETRY LOOP: Try up to 3 times to coerce the monitor
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # 1. Write the value
                proc = await asyncio.create_subprocess_exec(
                    "ddcutil", "--bus", str(bus_id), "setvcp", "10", str(target_brightness),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.wait_for(proc.wait(), timeout=2.0)
                
                # 2. WAIT: Give the hardware a moment to process the I2C command
                await asyncio.sleep(0.2)
                
                # 3. VERIFY: Read it back
                actual = await self.read_brightness(bus_id)
                
                # Success Check: Allow small difference (+/- 1) due to internal rounding
                if actual is not None and abs(actual - target_brightness) <= 1:
                    if attempt > 1:
                        logger.info(f"Bus {bus_id}: Coerced brightness to {actual} on attempt {attempt}")
                    return # Success!
                
                logger.warning(f"Bus {bus_id}: Mismatch (Set: {target_brightness}, Got: {actual}). Retrying {attempt}/{max_retries}...")
                
            except asyncio.TimeoutError:
                logger.warning(f"Bus {bus_id}: Write timeout on attempt {attempt}")
                try: proc.kill()
                except: pass
            except Exception as e:
                logger.warning(f"Bus {bus_id}: Write error: {e}")
                
        logger.error(f"Bus {bus_id}: Gave up after {max_retries} attempts. Monitor may be unresponsive.")
    
    def update_brightness(self, _object, _psspec):
        # When global brightness changes, update all monitors
        for monitor in self.monitors:
            monitor.set_property("brightness", self.brightness)