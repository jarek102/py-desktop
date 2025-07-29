import gi
import pathlib

from gi.repository import (
    Gtk,
    GObject,
    AstalBluetooth as Bluetooth,
)
from gi.repository.Gdk import Cursor

BASE_DIR = pathlib.Path(__file__).resolve().parent
UI_FILE = BASE_DIR / 'BluetoothDevice.ui'

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL

RW = GObject.ParamFlags.READWRITE

@Gtk.Template(filename=UI_FILE.as_posix())
class BluetoothDevice(Gtk.Box):
    __gtype_name__ = 'BluetoothDevice'
    
    name = GObject.Property(type=str)
    icon = GObject.Property(type=str)
    
    favorite = GObject.Property(type=bool, default=False)
    favorite_icon = GObject.Property(type=str, default="star-new-symbolic")
    
    def __init__(self,device:Bluetooth.Device,favorite = False,**kwargs):
        super().__init__(**kwargs)
        
        self.device = device
        device.bind_property("alias",self,"name",SYNC)
        device.bind_property("icon",self,"icon",SYNC , lambda _,icon : icon + "-symbolic")
        
        self.device_active()
        device.connect("notify::connected",self.device_active)
        
        self.favorite = favorite
        if self.favorite:
            self.favorite_icon = "starred-symbolic"
        else:
            self.favorite_icon =  "star-new-symbolic"
        
        self.click = Gtk.GestureClick()
        self.add_controller(self.click)
        self.click.connect("released",self.device_clicked)
        
    @Gtk.Template.Callback()
    def favorite(self, _) -> None:
        self.favorite = not self.favorite
        if self.favorite:
            self.favorite_icon = "starred-symbolic"
        else:
            self.favorite_icon =  "star-new-symbolic"
                
    @Gtk.Template.Callback()
    def unpair(self, _) -> None:
        self.device.cancel_pairing()
                
    def device_active(self, _obj = None, _data = None):
        if self.device.props.connected:
            self.get_style_context().add_class("active")
        else:
            self.get_style_context().remove_class("active")

    def device_clicked(self, _count, _x, _y, _) -> None:
        if self.device.props.connected:
            self.device.disconnect_device()
        else:
            self.device.connect_device()