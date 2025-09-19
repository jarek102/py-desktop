import asyncio
import re
from gi.repository import GObject

class BrightnessService(GObject.Object):
    
    brightness = GObject.Property(type=int)
    current_brightness = None
    busy = GObject.Property(type=bool,default=False)
    
    initialization_task = None
    update_tasks = []
    
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
        self.current_brightness = brightnness
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
    
    async def update(self, brightness):
        if self.initialization_task != None:
            await self.initialization_task
            self.initialization_task = None
        
        current_task = None
        
        for task in self.update_tasks:
            if task['value'] == brightness: 
                current_task = task
                continue
            await task['task']
        
        if self.current_brightness == brightness:
            self.update_tasks.remove(current_task)
            return
        
        for monitor in self.monitors:
            await self.write_brightness(monitor,brightness)
        self.current_brightness = brightness
        
        self.update_tasks.remove(current_task)
    
    def update_brightness(self,_object,_psspec):
        brightness = self.brightness
        for task in self.update_tasks:
            if task['value'] == brightness: return
        
        self.update_tasks.append({
            "task" : asyncio.create_task(self.update(brightness)),
            "value" : brightness
        })
        