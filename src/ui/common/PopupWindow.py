import gi
from gi.repository import Astal, Gtk

class PopupWindow:
    """
    Mixin to configure a window as a popup.
    Sets layer to OVERLAY.
    Click-outside handling is managed by App overlays.
    """
    def setup_popup(self):
        self.set_layer(Astal.Layer.OVERLAY)