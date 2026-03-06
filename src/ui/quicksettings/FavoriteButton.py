import versions
from gi.repository import Gtk, GObject, AstalBluetooth as Bluetooth
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE


@Blueprint("quicksettings/FavoriteButton.blp")
class FavoriteButton(Gtk.ToggleButton):
    __gtype_name__ = "FavoriteButton"

    icon_name = GObject.Property(type=str, default="")

    def __init__(self, bt_device: "BluetoothDevice", **kwargs) -> None:  # noqa: F821
        super().__init__(**kwargs)
        self._bt_device = bt_device
        # Reflect the device's current icon in the button
        bt_device.bind_property("icon", self, "icon_name", SYNC)
        # Reflect the device's connected state in the toggle active state
        bt_device.device.bind_property("connected", self, "active", SYNC)

    @Gtk.Template.Callback()
    def on_clicked(self, _button: Gtk.ToggleButton) -> None:
        self._bt_device.device_clicked()
