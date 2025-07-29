import gi
import pathlib

from gi.repository import (
    Gtk,
    GObject,
    AstalBluetooth as Bluetooth,
)
from gi.repository.Gdk import Cursor
from ui.BluetoothDevice import BluetoothDevice

BASE_DIR = pathlib.Path(__file__).resolve().parent
UI_FILE = BASE_DIR / 'BluetoothMenu.ui'

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL

RW = GObject.ParamFlags.READWRITE

@Gtk.Template(filename=UI_FILE.as_posix())
class BluetoothMenu(Gtk.Box):
    __gtype_name__ = 'BluetoothMenu'
    
    bluetooth_devices_revealer = Gtk.Template.Child(name='bluetooth-devices')
    devices = Gtk.Template.Child()
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        
        for device in Bluetooth.get_default().get_devices():
            self.devices.append(BluetoothDevice(device))
            
    @Gtk.Template.Callback()
    def bluetooth_toggle(self, _scale, _type, value) -> None:
        Bluetooth.get_default().toggle()
        
    @Gtk.Template.Callback()
    def show_devices(self, button) -> None:
        reveal = self.bluetooth_devices_revealer.get_reveal_child()
        if (reveal):
            button.set_icon_name("go-down-symbolic")
        else:
            button.set_icon_name("go-up-symbolic")
        self.bluetooth_devices_revealer.set_reveal_child(not reveal)