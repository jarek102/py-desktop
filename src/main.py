#!/usr/bin/env python3

from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')

import pathlib

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
gi.require_version('Astal','4.0')

from gi.repository import Astal, Gtk, Gio
from ui.DeviceMenu import DeviceMenu
from ui.Bar import Bar

BASE_DIR = pathlib.Path(__file__).resolve().parent
CSS_FILE = BASE_DIR / 'ui' / 'style.css'

class App(Astal.Application):
    devmenu = None
    bar = {}
    
    def __init__(self, **kwargs):
        super().__init__(
            instance_name = "py_desktop",
            application_id='com.github.jarek102.py-desktop',
            **kwargs)
        self.connect('activate', self.on_activate)
    
    def on_activate(self,_):
        if not self.devmenu:
            self.apply_css(CSS_FILE.as_posix(), True)
            self.devmenu = DeviceMenu()
            self.add_window(self.devmenu)
        if not self.bar:
            for mon in self.get_monitors():
                self.bar[mon] = Bar(gdkmonitor=mon)
                self.add_window(self.bar[mon])
        self.devmenu.present()
        for b in self.bar.values():
            b.present()
        
        
        
    def do_astal_application_request(self, msg: str, conn: Gio.SocketConnection) -> None:
        print(msg)
        AstalIO.write_sock(conn, "hello")


if __name__ == "__main__":
    app = App()
    app.run(None)