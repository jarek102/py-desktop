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
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.favorites: dict = {}
        self.settings = Gio.Settings.new("com.github.jarek102.py-desktop")
        self.favorites_store = set(self.settings.get_strv("bluetooth-favorites"))
        
        self.bluetooth = Bluetooth.get_default()
        
        for device in self.bluetooth.get_devices():
            bt_device = BluetoothDevice(device)
            self.devices.append(bt_device)
            bt_device.connect("notify::favorite",self.make_favorite)
            
            if bt_device.device.props.address in self.favorites_store:  # type: ignore[reportAttributeAccessIssue]
                bt_device.favorite = True
            
        self.bluetooth.bind_property("is-powered", self.toggle, "active", SYNC)
    def make_favorite(self, bt_device: BluetoothDevice, _data=None) -> None:
        address = bt_device.device.props.address  # type: ignore[reportAttributeAccessIssue]
        if bt_device.favorite:
            if bt_device not in self.favorites:
                button = Gtk.ToggleButton(icon_name=bt_device.icon)
                button.connect("clicked", lambda _btn: bt_device.device_clicked())
                bt_device.device.bind_property("connected", button, "active", SYNC)
                self.favorites[bt_device] = button
                self.header.insert_child_after(button, self.toggle)
            self.favorites_store.add(address)
        else:
            if bt_device in self.favorites:
                self.header.remove(self.favorites.pop(bt_device))
            self.favorites_store.discard(address)
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