import asyncio
import re
import shutil
import logging
from gi.repository import GObject

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BrightnessService")

class BrightnessService(GObject.Object):
    
    brightness = GObject.Property(type=int)
    current_brightness = None
    busy = GObject.Property(type=bool, default=False)
    
    initialization_task = None
    _update_task = None
    
    monitors = []
        
    def __init__(self):
        super().__init__()
        
        if not shutil.which("ddcutil"):
            logger.error("ddcutil executable not found")
            return

        self.connect('notify::brightness', self.update_brightness)
        self.initialization_task = asyncio.create_task(self.initialize())
        
    async def initialize(self):
        self.busy = True
        try:
            detect = await asyncio.create_subprocess_exec(
                "ddcutil", "--terse", "detect",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await detect.communicate()
            output = stdout.decode()
            
            if detect.returncode != 0:
                logger.error(f"ddcutil detect failed: {stderr.decode()}")

            # Regex for "I2C bus: /dev/i2c-X"
            regex = r"I2C bus:\s+/dev/i2c-(\d+)"
            
            self.monitors = []
            for match in re.finditer(regex, output):
                self.monitors.append(match.group(1))
            
            logger.info(f"Detected Monitor Buses: {self.monitors}")

            if self.monitors:
                val = await self.read_brightness(self.monitors[0])
                if val is not None:
                    self.current_brightness = val
                    self.set_property("brightness", val)
            
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
    
    async def _worker_loop(self):
        if self.initialization_task:
            await self.initialization_task
        
        while self.brightness != self.current_brightness:
            target = self.brightness
            
            # Run robust write logic in parallel for all monitors
            tasks = [self.write_brightness(bus, target) for bus in self.monitors]
            if tasks:
                await asyncio.gather(*tasks)
            
            # Even if it failed, we update current_brightness to stop the loop
            # forcing the user to move the slider again if they really want to retry manually
            self.current_brightness = target
    
    def update_brightness(self, _object, _psspec):
        # Drop updates if we are already busy to prevent queueing up laggy operations
        if self._update_task is None or self._update_task.done():
            self._update_task = asyncio.create_task(self._worker_loop())