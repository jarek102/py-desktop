import gi

from gi.repository import (
    Gtk,
    GObject,
    Gio,
    AstalBluetooth as Bluetooth,
)

from ui.BluetoothDevice import BluetoothDevice
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL

RW = GObject.ParamFlags.READWRITE

@Blueprint("BluetoothMenu.blp")
class BluetoothMenu(Gtk.Box):
    __gtype_name__ = 'BluetoothMenu'
    
    revealer = Gtk.Template.Child()
    devices = Gtk.Template.Child()
    toggle = Gtk.Template.Child()
    buttons = Gtk.Template.Child()
    
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
            
        self.bluetooth_active()
        self.bluetooth.connect("notify::is-powered",self.bluetooth_active)
    
    def update_active(self,widget,state):
        if state:
            widget.get_style_context().add_class("active")
        else:
            widget.get_style_context().remove_class("active")

    def bluetooth_active(self, _obj = None, _data = None):
        self.update_active(self.toggle,self.bluetooth.props.is_powered)
            
    def make_favorite(self, bt_device : BluetoothDevice, _data = None):
        address = bt_device.device.props.address
        if bt_device.favorite:
            button = Gtk.Button(icon_name=bt_device.icon)
            button.connect("clicked",lambda _button: bt_device.device_clicked())
            bt_device.device.connect("notify::connected",lambda device,_data: self.update_active(button,device.props.connected))
            self.update_active(button,bt_device.device.props.connected)
            self.favorites[bt_device] = button
            self.buttons.insert_child_after(button,self.toggle)
            self.favorites_store.add(address)
        else:
            self.buttons.remove(self.favorites[bt_device])
            self.favorites.pop(bt_device)
            if address in self.favorites_store:
                self.favorites_store.remove(address)
        self.settings.set_strv("bluetooth-favorites", list(self.favorites_store))
            
    @Gtk.Template.Callback()
    def bluetooth_toggle(self, _scale, _type, value) -> None:
        self.bluetooth.toggle()
        
    @Gtk.Template.Callback()
    def show_devices(self, button) -> None:
        reveal = self.revealer.get_reveal_child()
        if (reveal):
            button.set_icon_name("go-down-symbolic")
        else:
            button.set_icon_name("go-up-symbolic")
        self.revealer.set_reveal_child(not reveal)