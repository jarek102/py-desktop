import logging
from gi.repository import Gtk, GObject, AstalNetwork
from utils import Blueprint

_log = logging.getLogger("py_desktop.wifi_ap_item")

SYNC = GObject.BindingFlags.SYNC_CREATE


@Blueprint("quicksettings/WifiApItem.blp")
class WifiApItem(Gtk.ToggleButton):
    __gtype_name__ = "WifiApItem"

    icon_name = GObject.Property(type=str, default="network-wireless-symbolic")
    ssid = GObject.Property(type=str, default="")
    strength_label = GObject.Property(type=str, default="")
    is_active = GObject.Property(type=bool, default=False)
    requires_password = GObject.Property(type=bool, default=False)

    def __init__(self, ap: AstalNetwork.AccessPoint, active_ap, **kwargs):
        super().__init__(**kwargs)
        self._ap = ap
        self._handler_ids: list[int] = []

        raw_ssid = ap.get_ssid()
        self.ssid = raw_ssid if raw_ssid else "Hidden Network"
        self.strength_label = f"{ap.get_strength()}%"
        self.is_active = (
            active_ap is not None
            and ap.get_bssid() == active_ap.get_bssid()
        )

        ap.bind_property("icon-name", self, "icon_name", SYNC)
        ap.bind_property("requires-password", self, "requires_password", SYNC)
        self._handler_ids = [
            ap.connect("notify::ssid", self._on_ssid_changed),
            ap.connect("notify::strength", self._on_strength_changed),
        ]

        self.connect("clicked", self._on_clicked)

    def disconnect_signals(self) -> None:
        for hid in self._handler_ids:
            self._ap.disconnect(hid)
        self._handler_ids.clear()

    def _on_ssid_changed(self, ap, _pspec) -> None:
        raw = ap.get_ssid()
        self.ssid = raw if raw else "Hidden Network"

    def _on_strength_changed(self, ap, _pspec) -> None:
        self.strength_label = f"{ap.get_strength()}%"

    def _on_clicked(self, _) -> None:
        # Activate the saved connection for this AP (no-op if already active).
        # Password-protected unknown APs would require a dialog — deferred.
        try:
            self._ap.activate()  # type: ignore[reportAttributeAccessIssue]
        except Exception as e:
            _log.warning("Failed to activate AP %s: %s", self._ap.get_ssid(), e)
