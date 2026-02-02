import gi
from gi.repository import Astal, Gtk

class PopupWindow:
    """
    Mixin to configure a window as a popup.
    Sets layer to OVERLAY and default anchors.
    Click-outside handling is managed by App overlays.
    """
    def setup_popup(self):
        self.set_layer(Astal.Layer.OVERLAY)
        self.set_keymode(Astal.Keymode.ON_DEMAND)
        self.set_exclusivity(Astal.Exclusivity.IGNORE)
        
        if self.get_anchor() == Astal.WindowAnchor.NONE:
            self.set_anchor(Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT)
            self.set_margin_top(4)
            self.set_margin_right(4)