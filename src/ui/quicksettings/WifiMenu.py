import logging
from gi.repository import Gtk, GObject, AstalNetwork, Pango
from ui.common.PanelRow import PanelRow
from ui.quicksettings.WifiApItem import WifiApItem
from utils import Blueprint

_log = logging.getLogger("py_desktop.wifi_menu")

SYNC = GObject.BindingFlags.SYNC_CREATE


@Blueprint("quicksettings/WifiMenu.blp")
class WifiMenu(Gtk.Box):
    __gtype_name__ = "WifiMenu"

    panel_row = Gtk.Template.Child()

    icon_name = GObject.Property(type=str, default="network-wireless-offline-symbolic")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._wifi = AstalNetwork.get_default().get_wifi()

        if self._wifi is None:
            self.set_visible(False)
            return

        self._conn_label = Gtk.Label(hexpand=True, halign=Gtk.Align.START, xalign=0.0)
        self._conn_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.panel_row.set_content_widget(self._conn_label)

        self._wifi.bind_property("icon-name", self, "icon_name", SYNC)
        self._wifi.connect("notify::ssid", self._update_state)
        self._wifi.connect("notify::enabled", self._update_state)
        self._wifi.connect("notify::access-points", self._rebuild_ap_list)
        self.panel_row.connect("toggle-activated", self._on_toggle)
        self.panel_row.connect("icon-activated", self._on_icon_activated)

        self._update_state()
        self._rebuild_ap_list()

    def _update_state(self, *_args) -> None:
        ssid = self._wifi.get_ssid()
        if ssid:
            self._conn_label.set_label(ssid)
        elif self._wifi.get_enabled():
            self._conn_label.set_label("Not connected")
        else:
            self._conn_label.set_label("Wi-Fi off")
        self.panel_row.toggle_active = self._wifi.get_enabled()

    def _rebuild_ap_list(self, *_args) -> None:
        box = self.panel_row.revealer_box
        child = box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            if isinstance(child, WifiApItem):
                child.disconnect_signals()
            box.remove(child)
            child = nxt

        active_ap = self._wifi.get_active_access_point()
        aps = self._wifi.get_access_points()  # type: ignore[reportAttributeAccessIssue]
        if not aps:
            self.panel_row.chevron_visible = False
            return

        def _is_relevant(ap: AstalNetwork.AccessPoint) -> bool:
            return bool(ap.get_ssid())  # show all named APs; active shown first via sort

        def _sort_key(ap: AstalNetwork.AccessPoint):
            is_active = (
                active_ap is not None
                and ap.get_bssid() == active_ap.get_bssid()
            )
            return (not is_active, -ap.get_strength())

        relevant = sorted(
            [ap for ap in aps if _is_relevant(ap)],  # type: ignore[union-attr]
            key=_sort_key,
        )
        for ap in relevant:
            box.append(WifiApItem(ap, active_ap))

        self.panel_row.chevron_visible = len(relevant) > 0

    def _on_icon_activated(self, _panel_row: PanelRow) -> None:
        self._wifi.set_enabled(not self._wifi.get_enabled())

    def _on_toggle(self, _panel_row: PanelRow, active: bool) -> None:
        if active != self._wifi.get_enabled():
            self._wifi.set_enabled(active)
