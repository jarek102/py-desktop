import gi
from gi.repository import Gtk, GObject
from services.BrightnessService import BrightnessService
from ui.BrightnessItem import BrightnessItem
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL

@Blueprint("BrightnessMenu.blp")
class BrightnessMenu(Gtk.Box):
    __gtype_name__ = 'BrightnessMenu'
    
    revealer = Gtk.Template.Child()
    device_list = Gtk.Template.Child()
    expand = Gtk.Template.Child()
    slider = Gtk.Template.Child()
    icon = Gtk.Template.Child()
    
    icon_name = GObject.Property(type=str)
    value = GObject.Property(type=float)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = BrightnessService()
        
        self.icon.set_sensitive(False)
        self.icon_name = "display-brightness-symbolic"
        
        # Bind global brightness
        self.service.bind_property("brightness", self, "value", BIDI | SYNC)
        
        # Wait for initialization to populate list
        if self.service.initialization_task:
            self.service.initialization_task.add_done_callback(self.on_initialized)

    def on_initialized(self, task):
        for monitor in self.service.monitors:
            item = BrightnessItem(monitor)
            self.device_list.append(item)

    @Gtk.Template.Callback()
    def toggle_reveal(self, *args):
        reveal = self.revealer.get_reveal_child()
        if reveal:
            self.expand.set_icon_name("go-down-symbolic")
        else:
            self.expand.set_icon_name("go-up-symbolic")
        self.revealer.set_reveal_child(not reveal)