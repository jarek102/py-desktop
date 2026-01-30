import gi
from gi.repository import Astal, Gtk

class PopupWindow:
    """
    Mixin to handle click-outside-to-close behavior.
    Expected to be mixed into an Astal.Window.
    """
    def setup_popup(self):
        # Configure window to be fullscreen transparent overlay
        self.set_anchor(Astal.WindowAnchor.TOP | Astal.WindowAnchor.BOTTOM | Astal.WindowAnchor.LEFT | Astal.WindowAnchor.RIGHT)
        self.set_exclusivity(Astal.Exclusivity.IGNORE)
        self.set_keymode(Astal.Keymode.ON_DEMAND)

        # Setup click detection
        gesture = Gtk.GestureClick()
        gesture.connect("pressed", self._on_click_outside)
        self.add_controller(gesture)

        # Align content to Top-Right by default
        child = self.get_child()
        if child:
            child.set_halign(Gtk.Align.END)
            child.set_valign(Gtk.Align.START)

    def _on_click_outside(self, gesture, n_press, x, y):
        child = self.get_child()
        if not child:
            return
        
        allocation = child.get_allocation()
        # Check if click is outside the child widget's bounds
        if (x < allocation.x or x > allocation.x + allocation.width or
            y < allocation.y or y > allocation.y + allocation.height):
            self.hide()