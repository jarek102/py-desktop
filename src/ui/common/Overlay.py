import gi
from gi.repository import Astal, Gtk
from utils import Blueprint

@Blueprint("common/Overlay.blp")
class Overlay(Astal.Window):
    __gtype_name__ = "Overlay"

    def __init__(self, on_close, **kwargs):
        super().__init__(**kwargs)
        self._on_close = on_close

    @Gtk.Template.Callback()
    def on_pressed(self, *args):
        if self._on_close:
            self._on_close()