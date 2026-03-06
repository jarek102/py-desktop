import versions  # noqa: F401 — must precede gi.repository imports
import asyncio
import re
import shutil
import logging
import pathlib
from dataclasses import dataclass, field
from gi.repository import GObject
from gi.repository import GLib  # noqa: F401

logger = logging.getLogger("BrightnessService")

INTERNAL_CONNECTOR_PREFIXES = ("EDP", "LVDS", "DSI")

# ---------------------------------------------------------------------------
# DDC timing profiles
# Keyed by the manufacturer code — the first colon-delimited field from the
# "Monitor: MFG:Model:Serial" line in `ddcutil detect` output.
#
# --sleep-multiplier overrides ddcutil's default dynamic-sleep algorithm with
# a fixed multiplier, which improves reliability on monitors with slow DDC
# implementations (e.g. BenQ). The timeout must be scaled accordingly so we
# don't kill the subprocess before it finishes.
# ---------------------------------------------------------------------------

@dataclass
class DDCProfile:
    flags: list[str] = field(default_factory=list)
    timeout: float = 2.0


_DDC_PROFILES: dict[str, DDCProfile] = {
    "BNQ": DDCProfile(flags=["--sleep-multiplier", "3"], timeout=6.0),
}
_DDC_DEFAULT = DDCProfile()

_DETECT_MAX_TRIES = 3
_DETECT_RETRY_DELAY = 0.5


# ---------------------------------------------------------------------------
# Pure helper functions (tested in tests/unit/test_brightness_helpers.py)
# ---------------------------------------------------------------------------

def is_internal_connector(name: str | None) -> bool:
    if not name:
        return False
    upper = name.strip().upper()
    return upper.startswith(INTERNAL_CONNECTOR_PREFIXES)


def should_skip_ddc_display(connector: str | None, has_sysfs_internal: bool) -> bool:
    return has_sysfs_internal and is_internal_connector(connector)


def clamp_internal_percent(percent: int, min_percent: int = 1) -> int:
    return max(min_percent, min(100, int(percent)))


# ---------------------------------------------------------------------------
# Monitor backends
# ---------------------------------------------------------------------------

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
        self._update_task = asyncio.get_event_loop().create_task(self.worker())

    async def worker(self):
        target = clamp_internal_percent(self.brightness)
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
                val = max(1, min(self._max, val))
                with open(self.path / "brightness", "w") as f:
                    f.write(str(val))
        except Exception as e:
            logger.warning(f"Sysfs write failed: {e}")


class DDCMonitor(GObject.Object):
    bus_id = GObject.Property(type=str)
    name = GObject.Property(type=str)
    brightness = GObject.Property(type=int)

    def __init__(self, bus_id: str, name: str, current: int, service, profile: DDCProfile):
        super().__init__()
        self.bus_id = bus_id
        self.name = name
        self.service = service
        self.profile = profile
        self.brightness = current
        self._update_task = None
        self.connect("notify::brightness", self.on_change)

    def on_change(self, *args):
        if self._update_task is None or self._update_task.done():
            self._update_task = asyncio.get_event_loop().create_task(self.worker())

    async def worker(self):
        while True:
            target = self.brightness
            await self.service.write_brightness(self.bus_id, target, self.profile)
            if self.brightness == target:
                break


# ---------------------------------------------------------------------------
# Service (singleton)
# ---------------------------------------------------------------------------

class BrightnessService(GObject.Object):

    _instance = None

    brightness = GObject.Property(type=int)
    busy = GObject.Property(type=bool, default=False)

    @classmethod
    def get_default(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if BrightnessService._instance is not None:
            raise RuntimeError("BrightnessService is a singleton. Use BrightnessService.get_default()")
        super().__init__()

        self.monitors: list = []
        self.initialization_task = None

        self.connect('notify::brightness', self.update_brightness)
        self.initialization_task = asyncio.get_event_loop().create_task(self.initialize())

    async def initialize(self):
        self.busy = True
        self.monitors = []
        has_sysfs_internal = False

        try:
            # 1. Internal displays (sysfs backlight)
            bl_dir = pathlib.Path("/sys/class/backlight")
            if bl_dir.exists():
                for path in bl_dir.iterdir():
                    if (path / "brightness").exists():
                        self.monitors.append(SysfsMonitor(path))
                        has_sysfs_internal = True

            # 2. External displays (DDC/CI via ddcutil)
            if shutil.which("ddcutil"):
                output = await self._detect_displays()

                for d in output.split("Display "):
                    if not d.strip():
                        continue

                    bus_match = re.search(r"I2C bus:\s+/dev/i2c-(\d+)", d)
                    if not bus_match:
                        continue
                    bus_id = bus_match.group(1)

                    connector_match = re.search(r"DRM[ _]connector:\s+(.*)", d, re.IGNORECASE)
                    connector = connector_match.group(1).strip() if connector_match else f"Bus {bus_id}"
                    connector = re.sub(r"^card\d+-", "", connector)
                    if should_skip_ddc_display(connector, has_sysfs_internal):
                        logger.info("Skipping duplicate internal DDC display on %s", connector)
                        continue

                    # Manufacturer code: first colon-delimited field of "Monitor: MFG:Model:Serial"
                    mfg_match = re.search(r"Monitor:\s+([^:]+):", d)
                    mfg_code = mfg_match.group(1).strip() if mfg_match else ""

                    # Human-readable model name: second colon-delimited field
                    model_match = re.search(r"Monitor:\s+[^:]+:([^:]+):", d)
                    if model_match and model_match.group(1).strip():
                        name = f"{model_match.group(1).strip()} ({connector})"
                    else:
                        name = f"Monitor ({connector})"

                    profile = _DDC_PROFILES.get(mfg_code, _DDC_DEFAULT)
                    if profile is not _DDC_DEFAULT:
                        logger.info(
                            "Applying DDC profile for %s (%s): flags=%s timeout=%.1fs",
                            name, mfg_code, profile.flags, profile.timeout,
                        )

                    val = await self.read_brightness(bus_id, profile)
                    if val is None:
                        val = 50

                    self.monitors.append(DDCMonitor(bus_id, name, val, self, profile))

            logger.info("Detected monitors: %s", [m.name for m in self.monitors])

            if self.monitors:
                self.set_property("brightness", self.monitors[0].brightness)

        except Exception as e:
            logger.exception(f"Initialization error: {e}")
        finally:
            self.busy = False

    async def _detect_displays(self) -> str:
        """Run `ddcutil --terse detect`, retrying up to _DETECT_MAX_TRIES times."""
        for attempt in range(1, _DETECT_MAX_TRIES + 1):
            try:
                proc = await asyncio.create_subprocess_exec(
                    "ddcutil", "--terse", "detect",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                output = stdout.decode()

                if proc.returncode != 0:
                    logger.warning(
                        "ddcutil detect failed (attempt %d/%d): %s",
                        attempt, _DETECT_MAX_TRIES, stderr.decode().strip(),
                    )
                elif "Display " in output:
                    return output
                else:
                    logger.warning(
                        "ddcutil detect returned no displays (attempt %d/%d)",
                        attempt, _DETECT_MAX_TRIES,
                    )
            except Exception as e:
                logger.warning("ddcutil detect error (attempt %d/%d): %s", attempt, _DETECT_MAX_TRIES, e)

            if attempt < _DETECT_MAX_TRIES:
                await asyncio.sleep(_DETECT_RETRY_DELAY)

        logger.error("ddcutil detect failed after %d attempts", _DETECT_MAX_TRIES)
        return ""

    async def read_brightness(self, bus_id: str, profile: DDCProfile = _DDC_DEFAULT) -> int | None:
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                "ddcutil", "--bus", str(bus_id), "--terse", "getvcp", "10",
                *profile.flags,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=profile.timeout)

            # Format: "VCP 10 C <current> <max>"
            match = re.search(r"VCP 10 C (\d+)", stdout.decode())
            if match:
                return int(match.group(1))

        except asyncio.TimeoutError:
            logger.warning(f"Timeout reading brightness from bus {bus_id}")
            if proc is not None:
                try:
                    proc.kill()
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Error reading bus {bus_id}: {e}")
        return None

    async def write_brightness(
        self, bus_id: str, target_brightness: int, profile: DDCProfile = _DDC_DEFAULT
    ) -> None:
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            proc = None
            try:
                proc = await asyncio.create_subprocess_exec(
                    "ddcutil", "--bus", str(bus_id), "setvcp", "10", str(target_brightness),
                    *profile.flags,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await asyncio.wait_for(proc.wait(), timeout=profile.timeout)

                await asyncio.sleep(0.2)

                actual = await self.read_brightness(bus_id, profile)

                if actual is not None and abs(actual - target_brightness) <= 1:
                    if attempt > 1:
                        logger.info(f"Bus {bus_id}: Coerced brightness to {actual} on attempt {attempt}")
                    return

                logger.warning(
                    f"Bus {bus_id}: Mismatch (set={target_brightness}, got={actual}). "
                    f"Retrying {attempt}/{max_retries}..."
                )

            except asyncio.TimeoutError:
                logger.warning(f"Bus {bus_id}: Write timeout on attempt {attempt}")
                if proc is not None:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Bus {bus_id}: Write error: {e}")

        logger.error(f"Bus {bus_id}: Gave up after {max_retries} attempts. Monitor may be unresponsive.")

    def update_brightness(self, _object, _pspec):
        for monitor in self.monitors:
            monitor.set_property("brightness", self.brightness)
