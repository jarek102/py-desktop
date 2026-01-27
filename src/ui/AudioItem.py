import gi
from gi.repository import Gtk, GObject, AstalWp as Wp
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE

@Blueprint("AudioItem.blp")
class AudioItem(Gtk.Button):
    __gtype_name__ = 'AudioItem'
    
    name = GObject.Property(type=str)
    icon = GObject.Property(type=str)
    is_default = GObject.Property(type=bool, default=False)
    
    def __init__(self, endpoint: Wp.Endpoint, **kwargs):
        super().__init__(**kwargs)
        self.endpoint = endpoint
        
        # TODO: Implement robust name shortening (e.g. move device number to back)
        self.endpoint.bind_property("description", self, "name", SYNC)
        self.endpoint.bind_property("volume-icon", self, "icon", SYNC)
        self.endpoint.bind_property("is-default", self, "is-default", SYNC)
        
        self.connect("clicked", self.on_clicked)
        
    def on_clicked(self, _):
        self.endpoint.set_is_default(True)