import gi
from gi.repository import Gtk, GObject, AstalWp as Wp
from ui.quicksettings.AudioItem import AudioItem
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL

@Blueprint("quicksettings/VolumeMenu.blp")
class VolumeMenu(Gtk.Box):
    __gtype_name__ = 'VolumeMenu'
    
    revealer = Gtk.Template.Child()
    device_list = Gtk.Template.Child()
    expand = Gtk.Template.Child()
    slider = Gtk.Template.Child()
    icon = Gtk.Template.Child()
    
    icon_name = GObject.Property(type=str)
    value = GObject.Property(type=float)
    active_device_label = GObject.Property(type=str, default="")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wp = Wp.get_default()
        self.audio = self.wp.get_audio()
        self.endpoint = None
        self._bindings = []
        self.type = None

    def setup(self, type: str):
        self.type = type
        if type == "speaker":
            self.wp.connect("notify::default-speaker", self.on_default_changed)
            self.audio.connect("speaker-added", self.refresh_items)
            self.audio.connect("speaker-removed", self.refresh_items)
        elif type == "microphone":
            self.wp.connect("notify::default-microphone", self.on_default_changed)
            self.audio.connect("microphone-added", self.refresh_items)
            self.audio.connect("microphone-removed", self.refresh_items)
        
        self.bind_default()
        self.refresh_items()

    def bind_default(self):
        for b in self._bindings:
            b.unbind()
        self._bindings.clear()
        
        if self.type == "speaker":
            self.endpoint = self.wp.get_default_speaker()
        else:
            self.endpoint = self.wp.get_default_microphone()
            
        if self.endpoint:
            self._bindings = [
                self.endpoint.bind_property("volume-icon", self, "icon_name", SYNC),
                self.endpoint.bind_property("volume", self, "value", BIDI | SYNC),
                self.endpoint.bind_property("description", self, "active_device_label", SYNC)
            ]

    def on_default_changed(self, *args):
        self.bind_default()

    def refresh_items(self, *args):
        child = self.device_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.device_list.remove(child)
            child = next_child
            
        items = []
        if self.type == "speaker":
            items = self.audio.get_speakers()
        else:
            items = self.audio.get_microphones()
            
        if items:
            for item in items:
                row = AudioItem(item)
                self.device_list.append(row)

    @Gtk.Template.Callback()
    def toggle_mute(self, *args):
        if self.endpoint:
            self.endpoint.set_mute(not self.endpoint.get_mute())

    @Gtk.Template.Callback()
    def toggle_reveal(self, *args):
        reveal = self.revealer.get_reveal_child()
        if reveal:
            self.expand.set_icon_name("go-down-symbolic")
        else:
            self.expand.set_icon_name("go-up-symbolic")
        self.revealer.set_reveal_child(not reveal)
