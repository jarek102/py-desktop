import logging
import versions
from gi.repository import Gtk, GObject
from utils import Blueprint

_log = logging.getLogger("py_desktop.panel_row")

SYNC = GObject.BindingFlags.SYNC_CREATE


@Blueprint("common/PanelRow.blp")
class PanelRow(Gtk.Box):
    __gtype_name__ = "PanelRow"

    # Icon slot
    icon_name = GObject.Property(type=str, default="")
    icon_sensitive = GObject.Property(type=bool, default=True)

    # Toggle slot
    toggle_icon_name = GObject.Property(type=str, default="")
    toggle_active = GObject.Property(type=bool, default=False)
    toggle_visible = GObject.Property(type=bool, default=False)

    # Revealer
    has_revealer = GObject.Property(type=bool, default=False)
    revealed = GObject.Property(type=bool, default=False)

    # Caption
    caption = GObject.Property(type=str, default="")
    caption_visible = GObject.Property(type=bool, default=False)

    # Template children
    icon_button = Gtk.Template.Child()
    content_box = Gtk.Template.Child()
    toggle_button = Gtk.Template.Child()
    chevron_button = Gtk.Template.Child()
    caption_label = Gtk.Template.Child()
    revealer = Gtk.Template.Child()
    revealer_box = Gtk.Template.Child()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    # --- Public API for subclasses ---

    def set_content_widget(self, widget: Gtk.Widget) -> None:
        """Replace content_box contents with a single widget."""
        child = self.content_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.content_box.remove(child)
            child = next_child
        self.content_box.append(widget)

    def add_revealer_child(self, widget: Gtk.Widget) -> None:
        """Append a widget to the revealer body."""
        self.revealer_box.append(widget)

    def set_has_revealer(self, value: bool) -> None:
        self.has_revealer = value

    # --- Callbacks wired from Blueprint ---

    @Gtk.Template.Callback()
    def on_icon_clicked(self, _button: Gtk.Button) -> None:
        """Override in subclasses to handle icon button clicks."""

    @Gtk.Template.Callback()
    def on_toggle_clicked(self, _button: Gtk.ToggleButton) -> None:
        """Override in subclasses to handle toggle clicks."""

    @Gtk.Template.Callback()
    def on_chevron_clicked(self, _button: Gtk.Button) -> None:
        currently_revealed = self.revealer.get_reveal_child()
        new_state = not currently_revealed
        self.revealer.set_reveal_child(new_state)
        self.revealed = new_state
        self.chevron_button.set_icon_name(
            "go-up-symbolic" if new_state else "go-down-symbolic"
        )
        if self.caption:
            self.caption_visible = not new_state
        _log.debug(
            "PanelRow %s revealed=%s", self.__class__.__name__, new_state
        )
