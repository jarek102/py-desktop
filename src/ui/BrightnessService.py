import asyncio
from optparse import Option
from os import read
import re
from sys import stdout
from gi.events import GLibEventLoopPolicy
from gi.repository import GObject

class BrightnessService(GObject.Object):
    
    brightness = GObject.Property(type=int)
    busy = GObject.Property(type=bool,default=False)
    
    initialization_task = None
    update_task = None
    
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
            
        brightnness = await self.read_brightness(self.monitors[0])
        self.brightness = brightnness
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
    
    async def write_brightness(self,monitor,brightnness) -> None:
        ddcutil = await asyncio.create_subprocess_exec(
            "ddcutil",
            "-t",
            "-d",
            monitor,
            "set",
            "10",
            f"{brightnness}",
            stdout=asyncio.subprocess.PIPE
        )
        
        await ddcutil.wait()
    
    async def update(self, value):
        if self.initialization_task != None:
            await self.initialization_task
            self.initialization_task = None
        
        for monitor in self.monitors:
            await self.write_brightness(monitor,value)
    
    async def create_update(self, value):
        if self.update_task != None:
            await self.update_task
            self.update_task = None
            
        self.update_task = asyncio.create_task(self.update(value))
    
    def update_brightness(self,_object,_psspec):
        asyncio.create_task(self.create_update(self.brightness))