import logging
from gi.repository import Gtk, GObject
from utils import Blueprint

_log = logging.getLogger("py_desktop.panel_row")

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL


@Blueprint("common/PanelRow.blp")
class PanelRow(Gtk.Box):
    __gtype_name__ = "PanelRow"

    __gsignals__ = {
        "icon-activated":    (GObject.SignalFlags.RUN_FIRST, None, ()),
        "toggle-activated":  (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        "chevron-activated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    # Header chrome
    icon_name       = GObject.Property(type=str, default="")
    toggle_visible  = GObject.Property(type=bool, default=True)
    toggle_active   = GObject.Property(type=bool, default=False)
    chevron_visible = GObject.Property(type=bool, default=True)
    caption         = GObject.Property(type=str, default="")
    caption_visible = GObject.Property(type=bool, default=False)

    # Internal: chevron icon tracks revealed state
    chevron_icon = GObject.Property(type=str, default="go-down-symbolic")

    header_box     = Gtk.Template.Child()
    content_box    = Gtk.Template.Child()
    toggle_button  = Gtk.Template.Child()
    chevron_button = Gtk.Template.Child()
    caption_label  = Gtk.Template.Child()
    revealer       = Gtk.Template.Child()
    revealer_box   = Gtk.Template.Child()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def set_content_widget(self, widget: Gtk.Widget) -> None:
        """Replace the content area with widget (slider, label, etc.)."""
        child = self.content_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.content_box.remove(child)
            child = next_child
        self.content_box.append(widget)

    # --- Template callbacks ---

    @Gtk.Template.Callback()
    def on_icon_clicked(self, _button: Gtk.Button) -> None:
        self.emit("icon-activated")

    @Gtk.Template.Callback()
    def on_toggle_clicked(self, button: Gtk.ToggleButton) -> None:
        self.emit("toggle-activated", button.get_active())

    @Gtk.Template.Callback()
    def on_chevron_clicked(self, _button: Gtk.Button) -> None:
        revealed = self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(not revealed)
        self.chevron_icon = "go-up-symbolic" if not revealed else "go-down-symbolic"
        self.emit("chevron-activated")
