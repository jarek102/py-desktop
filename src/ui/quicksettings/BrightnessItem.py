import gi
from gi.repository import Gtk, GObject
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL

@Blueprint("quicksettings/BrightnessItem.blp")
class BrightnessItem(Gtk.Box):
    __gtype_name__ = 'BrightnessItem'
    
    name = GObject.Property(type=str)
    brightness = GObject.Property(type=int)
    
    def __init__(self, monitor, **kwargs):
        super().__init__(**kwargs)
        monitor.bind_property("name", self, "name", SYNC)
        monitor.bind_property("brightness", self, "brightness", BIDI | SYNC)