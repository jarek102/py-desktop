import asyncio
import re
from gi.repository import GObject

class BrightnessService(GObject.Object):
    
    brightness = GObject.Property(type=int)
    current_brightness = None
    busy = GObject.Property(type=bool,default=False)
    
    initialization_task = None
    _update_task = None
    
    monitors = []
        
    def __init__(self):
        super().__init__()
        
        self.connect('notify::brightness',self.update_brightness)
        self.initialization_task = asyncio.create_task(self.initialize())
        
    async def initialize(self):
        self.busy = True
        detect = await asyncio.create_subprocess_exec(
            "ddcutil",
            "-t",
            "detect",
            stdout=asyncio.subprocess.PIPE
        )
        
        stdout, _ = await detect.communicate()
        
        regex = r"Display (\d+)"
        
        for match in re.finditer(regex,stdout.decode()):
            self.monitors.append(match.group(1))
        
        brightness = await self.read_brightness(self.monitors[0])
        self.current_brightness = brightness
        self.brightness = brightness
        self.busy = False
        
    async def read_brightness(self,monitor) -> int | None:
        ddcutil = await asyncio.create_subprocess_exec(
            "ddcutil",
            "-t",
            "-d",
            monitor,
            "get",
            "10",
            stdout=asyncio.subprocess.PIPE
        )
        
        stdout, _ = await ddcutil.communicate()
        
        regex = r"VCP 10 C (\d+) 100"
        
        for match in re.finditer(regex,stdout.decode()):
            return int(match.group(1))
    
    async def write_brightness(self,monitor,brightness) -> None:
        ddcutil = await asyncio.create_subprocess_exec(
            "ddcutil",
            "-t",
            "-d",
            monitor,
            "set",
            "10",
            f"{brightness}",
            stdout=asyncio.subprocess.PIPE
        )
        
        await ddcutil.wait()
    
    async def _worker_loop(self):
        if self.initialization_task is not None:
            await self.initialization_task
        
        while self.brightness != self.current_brightness:
            target = self.brightness
            for monitor in self.monitors:
                await self.write_brightness(monitor, target)
            self.current_brightness = target
    
    def update_brightness(self,_object,_psspec):
        if self._update_task is None or self._update_task.done():
            self._update_task = asyncio.create_task(self._worker_loop())