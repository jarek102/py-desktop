import logging
from gi.repository import Gtk, GObject, AstalBattery
from ui.quicksettings.BatteryDeviceItem import BatteryDeviceItem
from utils import Blueprint

_log = logging.getLogger("py_desktop.devices_menu")

# Device types that are power sources or infrastructure — not user peripherals.
# All other types (MOUSE, KEYBOARD, HEADPHONES, GAMING_INPUT, etc.) are shown.
_EXCLUDED_TYPES = {
    AstalBattery.Type.UNKNOWN,
    AstalBattery.Type.LINE_POWER,
    AstalBattery.Type.BATTERY,
    AstalBattery.Type.UPS,
    AstalBattery.Type.MONITOR,
}


@Blueprint("quicksettings/DevicesMenu.blp")
class DevicesMenu(Gtk.Box):
    __gtype_name__ = "DevicesMenu"

    panel_row = Gtk.Template.Child()

    icon_name = GObject.Property(type=str, default="battery-symbolic")
    has_multiple = GObject.Property(type=bool, default=False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._upower = AstalBattery.UPower.new()  # type: ignore[reportAttributeAccessIssue]

        # Content widget: summary label in the PanelRow header
        self._summary_label = Gtk.Label(hexpand=True, halign=Gtk.Align.START, xalign=0.0)
        self.panel_row.set_content_widget(self._summary_label)

        self._upower.connect("notify::devices", self._refresh)
        self._refresh()

    def _get_peripheral_devices(self) -> list:
        devices = self._upower.get_devices()  # type: ignore[reportAttributeAccessIssue]
        if not devices:
            return []
        return [
            d for d in devices  # type: ignore[union-attr]
            if d.get_device_type() not in _EXCLUDED_TYPES and d.get_is_present()
        ]

    def _refresh(self, *_args) -> None:
        devices = self._get_peripheral_devices()

        if not devices:
            self.set_visible(False)
            return

        self.set_visible(True)
        self.has_multiple = len(devices) > 1

        # Determine panel icon and summary label
        low_devices = [
            d for d in devices
            if d.get_warning_level() in (
                AstalBattery.WarningLevel.LOW,
                AstalBattery.WarningLevel.CRITICIAL,  # upstream typo
            )
        ]

        if low_devices:
            d = low_devices[0]
            name = d.get_model() or d.get_device_type_name() or "Device"
            self._summary_label.set_label(f"Low: {name}")
            self.icon_name = "battery-low-symbolic"
        elif len(devices) == 1:
            d = devices[0]
            name = d.get_model() or d.get_device_type_name() or "Device"
            self._summary_label.set_label(name)
            self.icon_name = d.get_device_type_icon() or "battery-symbolic"
        else:
            self._summary_label.set_label(f"{len(devices)} devices")
            self.icon_name = "battery-symbolic"

        # Rebuild the revealer list; disconnect old items' signals first to
        # prevent the long-lived Device objects from keeping them alive.
        box = self.panel_row.revealer_box
        child = box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            if isinstance(child, BatteryDeviceItem):
                child.disconnect_signals()
            box.remove(child)
            child = nxt

        for device in devices:
            box.append(BatteryDeviceItem(device))
