import gi

from gi.repository import (
    Gtk,
    GObject,
    Gio,
    AstalBluetooth as Bluetooth,
)

from ui.quicksettings.BluetoothDevice import BluetoothDevice
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL

RW = GObject.ParamFlags.READWRITE

@Blueprint("quicksettings/BluetoothMenu.blp")
class BluetoothMenu(Gtk.Box):
    __gtype_name__ = 'BluetoothMenu'
    
    revealer = Gtk.Template.Child()
    devices = Gtk.Template.Child()
    toggle = Gtk.Template.Child()
    header = Gtk.Template.Child()
    expand = Gtk.Template.Child()
    
    favorites = {}
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        
        self.settings = Gio.Settings.new("com.github.jarek102.py-desktop")
        self.favorites_store = set(self.settings.get_strv("bluetooth-favorites"))
        
        self.bluetooth = Bluetooth.get_default()
        
        for device in self.bluetooth.get_devices():
            bt_device = BluetoothDevice(device)
            self.devices.append(bt_device)
            bt_device.connect("notify::favorite",self.make_favorite)
            
            if bt_device.device.props.address in self.favorites_store:
                bt_device.favorite = True
            
        self.bluetooth.bind_property("is-powered", self.toggle, "active", SYNC)
    def make_favorite(self, bt_device : BluetoothDevice, _data = None):
        address = bt_device.device.props.address
        if bt_device.favorite:
            button = Gtk.ToggleButton(icon_name=bt_device.icon)
            button.connect("clicked", lambda _button: bt_device.device_clicked())
            # Bind the device's connected state straight to the button's active state
            bt_device.device.bind_property("connected", button, "active", SYNC)
            self.favorites[bt_device] = button
            self.header.insert_child_after(button,self.toggle)
            self.favorites_store.add(address)
        else:
            self.header.remove(self.favorites[bt_device])
            self.favorites.pop(bt_device)
            if address in self.favorites_store:
                self.favorites_store.remove(address)
        self.settings.set_strv("bluetooth-favorites", list(self.favorites_store))
            
    @Gtk.Template.Callback()
    def bluetooth_toggle(self, *args) -> None:
        self.bluetooth.toggle()
        
    @Gtk.Template.Callback()
    def toggle_reveal(self, *args) -> None:
        reveal = self.revealer.get_reveal_child()
        if reveal:
            self.expand.set_icon_name("go-down-symbolic")
        else:
            self.expand.set_icon_name("go-up-symbolic")
        self.revealer.set_reveal_child(not reveal)