import logging
from gi.repository import Gtk, GObject, AstalNetwork, Pango
from ui.common.PanelRow import PanelRow
from utils import Blueprint

_log = logging.getLogger("py_desktop.wired_menu")

SYNC = GObject.BindingFlags.SYNC_CREATE


@Blueprint("quicksettings/WiredMenu.blp")
class WiredMenu(Gtk.Box):
    __gtype_name__ = "WiredMenu"

    panel_row = Gtk.Template.Child()

    icon_name = GObject.Property(type=str, default="network-wired-symbolic")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._wired = AstalNetwork.get_default().get_wired()

        if self._wired is None:
            self.set_visible(False)
            return

        self._conn_label = Gtk.Label(hexpand=True, halign=Gtk.Align.START, xalign=0.0)
        self._conn_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.panel_row.set_content_widget(self._conn_label)

        self._wired.bind_property("icon-name", self, "icon_name", SYNC)
        self._wired.connect("notify::state", self._update_state)
        self.panel_row.connect("icon-activated", self._on_icon_activated)

        self._update_state()

    def _update_state(self, *_args) -> None:
        state = self._wired.get_state()
        if state == AstalNetwork.DeviceState.ACTIVATED:
            self._conn_label.set_label("Wired")
        else:
            self._conn_label.set_label("Disconnected")

    def _on_icon_activated(self, _panel_row: PanelRow) -> None:
        self._wired.set_enabled(not self._wired.get_enabled())
