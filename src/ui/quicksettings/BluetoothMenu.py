import versions
from gi.repository import Gtk, GObject, Gio, AstalBluetooth as Bluetooth
from ui.quicksettings.BluetoothDevice import BluetoothDevice
from ui.quicksettings.FavoriteButton import FavoriteButton
from ui.common.PanelRow import PanelRow

SYNC = GObject.BindingFlags.SYNC_CREATE


class BluetoothMenu(PanelRow):
    __gtype_name__ = "BluetoothMenu"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.favorites: dict = {}

        self.icon_name = "bluetooth-active-symbolic"
        self.toggle_icon_name = "bluetooth-active-symbolic"
        self.toggle_visible = True
        self.set_has_revealer(True)

        self.settings = Gio.Settings.new("com.github.jarek102.py-desktop")
        self.favorites_store = set(self.settings.get_strv("bluetooth-favorites"))

        self.bluetooth = Bluetooth.get_default()
        self.bluetooth.bind_property("is-powered", self, "toggle_active", SYNC)

        for device in self.bluetooth.get_devices():
            self._add_device(device)

        self.bluetooth.connect("device-added", self._on_device_added)

    def _add_device(self, device: Bluetooth.Device) -> None:
        bt_device = BluetoothDevice(device)
        self.add_revealer_child(bt_device)
        bt_device.connect("notify::favorite", self._on_make_favorite)
        if bt_device.device.props.address in self.favorites_store:
            bt_device.favorite = True

    def _on_device_added(self, _bluetooth, device: Bluetooth.Device) -> None:
        self._add_device(device)

    def _on_make_favorite(
        self, bt_device: BluetoothDevice, _data=None
    ) -> None:
        address = bt_device.device.props.address
        if bt_device.favorite:
            favorite_button = FavoriteButton(bt_device)
            self.favorites[bt_device] = favorite_button
            self.content_box.append(favorite_button)
            self.favorites_store.add(address)
        else:
            button = self.favorites.pop(bt_device, None)
            if button is not None:
                self.content_box.remove(button)
            self.favorites_store.discard(address)
        self.settings.set_strv(
            "bluetooth-favorites", list(self.favorites_store)
        )

    def on_toggle_clicked(self, _button: Gtk.ToggleButton) -> None:
        self.bluetooth.toggle()
