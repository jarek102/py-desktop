from gi.repository import Gtk, GObject, AstalBattery
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE


@Blueprint("quicksettings/BatteryDeviceItem.blp")
class BatteryDeviceItem(Gtk.Box):
    __gtype_name__ = "BatteryDeviceItem"

    icon_name = GObject.Property(type=str, default="battery-symbolic")
    device_name = GObject.Property(type=str, default="")
    percentage_label = GObject.Property(type=str, default="")
    level = GObject.Property(type=float, default=0.0)

    def __init__(self, device: AstalBattery.Device, **kwargs):
        super().__init__(**kwargs)
        self._device = device

        self.icon_name = device.get_device_type_icon() or "battery-symbolic"
        self.device_name = device.get_model() or device.get_device_type_name() or "Unknown"
        self._update_percentage()

        self._handler_id = device.connect("notify::percentage", self._on_percentage_changed)

    def disconnect_signals(self) -> None:
        """Disconnect GObject signal handlers.

        Call before removing this widget from the revealer, otherwise the
        long-lived Device object keeps a reference to the discarded item.
        """
        if self._handler_id:
            self._device.disconnect(self._handler_id)
            self._handler_id = 0

    def _update_percentage(self) -> None:
        # get_percentage() returns 0.0–1.0
        pct = self._device.get_percentage()
        self.level = pct
        self.percentage_label = f"{round(pct * 100)}%"

    def _on_percentage_changed(self, _device, _pspec) -> None:
        self._update_percentage()
