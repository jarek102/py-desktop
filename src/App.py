import pathlib

from gi.repository import Astal, Gio, AstalIO
from ui.DeviceMenu import DeviceMenu
from ui.Bar import Bar

BASE_DIR = pathlib.Path(__file__).resolve().parent
CSS_FILE = BASE_DIR / 'ui' / 'style.css'

class App(Astal.Application):
    system_menu = None
    bars = {}
    
    def __init__(self, **kwargs):
        super().__init__(
            instance_name = "py_desktop",
            application_id='com.github.jarek102.py-desktop',
            **kwargs)
        self.connect('activate', self.on_activate)
    
    def on_activate(self,_):
        self.apply_css(CSS_FILE.as_posix(), True)
        if not self.bars:
            for mon in self.get_monitors():
                self.bars[mon] = Bar(gdkmonitor=mon,window_manager=self)
                self.add_window(self.bars[mon])
        for bar in self.bars.values():
            bar.present()
        
    def toggle_device_menu(self, gdkmonitor=None):
        if not self.system_menu:
            self.system_menu = DeviceMenu()
            self.add_window(self.system_menu)
        if gdkmonitor is not None and self.system_menu.get_monitor() != gdkmonitor:
            self.system_menu.set_monitor(gdkmonitor)
        
        if self.system_menu.is_visible():
            self.system_menu.hide()
        else:
            self.system_menu.present()
        
    def do_astal_application_request(self, msg: str, conn: Gio.SocketConnection) -> None:
        print(msg)
        AstalIO.write_sock(conn, "hello")