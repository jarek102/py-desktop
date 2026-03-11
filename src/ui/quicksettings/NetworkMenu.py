import logging
from gi.repository import Gtk, GObject, AstalNetwork, Pango
from ui.common.PanelRow import PanelRow
from ui.quicksettings.WifiApItem import WifiApItem
from utils import Blueprint

_log = logging.getLogger("py_desktop.network_menu")

SYNC = GObject.BindingFlags.SYNC_CREATE


@Blueprint("quicksettings/NetworkMenu.blp")
class NetworkMenu(Gtk.Box):
    __gtype_name__ = "NetworkMenu"

    panel_row = Gtk.Template.Child()

    icon_name = GObject.Property(type=str, default="network-wireless-offline-symbolic")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._nw = AstalNetwork.get_default()
        self._wifi = self._nw.get_wifi()
        self._wired = self._nw.get_wired()

        # Hide entire panel if no network hardware is present
        if self._wifi is None and self._wired is None:
            self.set_visible(False)
            return

        # Content widget: label showing the active connection name
        self._conn_label = Gtk.Label(hexpand=True, halign=Gtk.Align.START, xalign=0.0)
        self._conn_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.panel_row.set_content_widget(self._conn_label)

        self._nw.connect("notify::primary", self._on_primary_changed)

        if self._wifi is not None:
            self._wifi.connect("notify::ssid", self._update_state)
            self._wifi.connect("notify::enabled", self._update_state)
            self._wifi.connect("notify::icon-name", self._update_state)
            self._wifi.connect("notify::access-points", self._rebuild_ap_list)
            self.panel_row.connect("toggle-activated", self._on_toggle)
            self.panel_row.connect("chevron-activated", self._on_chevron)
        else:
            # Ethernet only — no toggle or AP list
            self.panel_row.toggle_visible = False
            self.panel_row.chevron_visible = False

        if self._wired is not None:
            self._wired.connect("notify::state", self._update_state)
            self._wired.connect("notify::icon-name", self._update_state)

        self._update_state()
        self._rebuild_ap_list()

    def _update_state(self, *_args) -> None:
        primary = self._nw.get_primary()

        if primary == AstalNetwork.Primary.WIRED and self._wired is not None:
            self.icon_name = self._wired.get_icon_name() or "network-wired-symbolic"
            ssid = self._wifi.get_ssid() if self._wifi else None
            label = f"Wired + {ssid}" if ssid else "Wired"
            self._conn_label.set_label(label)
        elif self._wifi is not None:
            self.icon_name = self._wifi.get_icon_name() or "network-wireless-offline-symbolic"
            ssid = self._wifi.get_ssid()
            if ssid:
                self._conn_label.set_label(ssid)
            elif self._wifi.get_enabled():
                self._conn_label.set_label("Not connected")
            else:
                self._conn_label.set_label("Wi-Fi off")
            # Sync toggle state without triggering the activated signal
            self.panel_row.toggle_active = self._wifi.get_enabled()
        else:
            self.icon_name = "network-offline-symbolic"
            self._conn_label.set_label("No network")

    def _on_primary_changed(self, *_args) -> None:
        self._update_state()
        self._rebuild_ap_list()

    def _rebuild_ap_list(self, *_args) -> None:
        if self._wifi is None:
            return

        box = self.panel_row.revealer_box
        child = box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            box.remove(child)
            child = nxt

        # Hide AP list when wired is the primary connection
        if self._nw.get_primary() == AstalNetwork.Primary.WIRED:
            self.panel_row.chevron_visible = False
            return

        active_ap = self._wifi.get_active_access_point()
        aps = self._wifi.get_access_points()  # type: ignore[reportAttributeAccessIssue]
        if not aps:
            self.panel_row.chevron_visible = False
            return

        # chevron_visible is always set unconditionally at the end of this
        # method, so do not assign it in early-exit paths beyond this point.

        def _is_relevant(ap: AstalNetwork.AccessPoint) -> bool:
            """Show APs with a saved NM connection, or hidden APs (empty SSID)."""
            if not ap.get_ssid():
                return True  # hidden network — always show
            try:
                conns = ap.get_connections()  # type: ignore[reportAttributeAccessIssue]
                return bool(conns)
            except Exception:
                return False

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

    def _on_toggle(self, _panel_row: PanelRow, active: bool) -> None:
        # Guard prevents a feedback loop: programmatic toggle_active changes
        # (from _update_state) also fire toggle-activated via the bidirectional
        # Blueprint binding; only call set_enabled when the state actually differs.
        if self._wifi is not None and active != self._wifi.get_enabled():
            self._wifi.set_enabled(active)

    def _on_chevron(self, _panel_row: PanelRow) -> None:
        pass  # PanelRow handles reveal toggle internally
