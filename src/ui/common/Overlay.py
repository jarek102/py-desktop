import gi
from gi.repository import Astal, Gtk

class Overlay(Astal.Window):
    __gtype_name__ = "Overlay"

    def __init__(self, on_close, **kwargs):
        super().__init__(
            anchor=Astal.WindowAnchor.TOP | Astal.WindowAnchor.BOTTOM | Astal.WindowAnchor.LEFT | Astal.WindowAnchor.RIGHT, # pyright: ignore[reportOperatorIssue]
            layer=Astal.Layer.TOP,
            exclusivity=Astal.Exclusivity.IGNORE,
            keymode=Astal.Keymode.NONE,
            **kwargs
        )
        
        super().add_css_class("overlay")
        gesture = Gtk.GestureClick()
        gesture.connect("pressed", lambda *_: on_close())
        self.add_controller(gesture)