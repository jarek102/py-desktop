import logging

import gi
import versions
import pathlib
import asyncio
from gi.repository import Gtk, Astal, GLib

from ui.quicksettings.DeviceMenu import DeviceMenu
from ui.quicksettings.BrightnessMenu import BrightnessMenu
from ui.quicksettings.VolumeMenu import VolumeMenu
from ui.quicksettings.BluetoothMenu import BluetoothMenu

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
CSS_FILE = BASE_DIR / 'generated' / 'style.css'

class TestApp(Astal.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='com.github.jarek102.py-desktop.test.devicemenu', **kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, _):

        win = Gtk.Window(application=self)
        win.set_title("Device Menu Test")
        win.set_default_size(400, 800)
        win.set_resizable(False)

        if CSS_FILE.exists():
            self.apply_css(CSS_FILE.as_posix(), True)
        
        device_menu = DeviceMenu()
        win.set_child(device_menu)
        
        win.present()

def loop_step(loop):
    loop.call_soon(loop.stop)
    loop.run_forever()
    return True

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    GLib.timeout_add(10, loop_step, loop)

    logging.basicConfig(level=logging.INFO)

    # Run with `PYTHONPATH=src python3 src/testDeviceMenu.py`
    app = TestApp(instance_name='py_desktop_test_device_menu')
    app.run([])
