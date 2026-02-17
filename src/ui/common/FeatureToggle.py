import gi
from gi.repository import Gtk, GObject
from utils import Blueprint

@Blueprint("common/FeatureToggle.blp")
class FeatureToggle(Gtk.ToggleButton):
    __gtype_name__ = 'FeatureToggle'

    icon_name = GObject.Property(type=str)
    label = GObject.Property(type=str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
