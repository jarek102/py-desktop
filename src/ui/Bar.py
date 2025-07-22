import math
import pathlib
from typing import Optional
from gi.repository import (
    Astal,
    AstalIO,
    GObject,
    GLib,
    Gtk,
    GObject,
    AstalBattery,
    AstalWp,
    AstalNetwork,
    AstalMpris,
    AstalPowerProfiles,
    AstalTray,
    AstalBluetooth,
)

from .WindowManager import WindowManager

SYNC = GObject.BindingFlags.SYNC_CREATE

BASE_DIR = pathlib.Path(__file__).resolve().parent
UI_FILE = BASE_DIR / 'Bar.ui'

@Gtk.Template(filename=UI_FILE.as_posix())
class Bar(Astal.Window):
    __gtype_name__ = "Bar"
    
    window_manager = None

    clock = GObject.Property(type=str)
    volume_icon = GObject.Property(type=str)
    battery_visible = GObject.Property(type=bool, default=False)
    battery_label = GObject.Property(type=str)
    battery_icon = GObject.Property(type=str)
    network_icon = GObject.Property(type=str)
    power_profile_icon = GObject.Property(type=str)
    bluetooth_visible = GObject.Property(type=bool, default=False)

    popover = Gtk.Template.Child()
    calendar = Gtk.Template.Child()
    traybox = Gtk.Template.Child()

    def __init__(self,window_manager: Optional[WindowManager] = None,**kwargs) -> None:
        super().__init__(
            anchor=Astal.WindowAnchor.TOP
            | Astal.WindowAnchor.LEFT # pyright: ignore[reportOperatorIssue]
            | Astal.WindowAnchor.RIGHT,
            exclusivity=Astal.Exclusivity.EXCLUSIVE,
            css_classes=["Bar"],
            visible=True,
            **kwargs
        )
        
        self.window_manager = window_manager

        # clock
        timer = AstalIO.Time.interval(1000, self.set_clock)
        self.connect("destroy", lambda _: timer.cancel())

        # everytime popover is opened, select current day
        self.popover.connect("notify::visible", self.on_popover_visible)

        # network
        nw = AstalNetwork.get_default()
        self._network_binding = None

        nw.bind_property(
            "primary",
            self,
            "network-icon",
            SYNC,
            self.on_nm_primary,
            None,
        )

        # battery
        bat = AstalBattery.get_default()
        bat.bind_property("is-present", self, "battery-visible", SYNC)
        bat.bind_property("icon-name", self, "battery-icon", SYNC)
        bat.bind_property(
            "percentage",
            self,
            "battery-label",
            SYNC,
            lambda _, percentage: f"{math.floor(percentage * 100)}%",
            None,
        )

        # powerprofiles
        powerprofile = AstalPowerProfiles.get_default()
        powerprofile.bind_property("icon-name", self, "power-profile-icon", SYNC)
        
        # volume
        speaker = AstalWp.get_default().get_default_speaker()
        speaker.bind_property("volume-icon", self, "volume-icon", SYNC)

        # bluetooth
        bt = AstalBluetooth.get_default()
        bt.bind_property("is-connected", self, "bluetooth-visible", SYNC)

        # tray
        tray = AstalTray.get_default()
        self._tray_items = {}

        def on_tray_item_added(tray, id):
            item = tray.get_item(id)
            popover = Gtk.PopoverMenu.new_from_model(item.get_menu_model())
            icon = Gtk.Image()
            button = Gtk.MenuButton(popover=popover, child=icon)

            item.bind_property("gicon", icon, "gicon", SYNC)
            popover.insert_action_group("dbusmenu", item.get_action_group())
            item.connect(
                "notify::action-group",
                lambda *_: popover.insert_action_group(
                    "dbusmenu", item.get_action_group()
                ),
            )

            self._tray_items[id] = button
            self.traybox.append(button)

        def on_tray_item_removed(_tray, id):
            button = self._tray_items.get(id)
            if button:
                self.traybox.remove(button)
                button.run_dispose()
                del self._tray_items[id]

        tray.connect("item_added", on_tray_item_added)
        tray.connect("item_removed", on_tray_item_removed)
        self.connect(
            "destroy",
            lambda *_: (
                tray.disconnect(on_tray_item_added),
                tray.disconnect(on_tray_item_removed),
            ),
        )

    def on_popover_visible(self, popover, _pspec):
        if popover.get_visible():
            self.calendar.select_day(GLib.DateTime.new_now_local())

    def on_nm_primary(self, _binding, primary):
        nw = AstalNetwork.get_default()
        if self._network_binding is not None:
            self._network_binding.unbind()

        match primary:
            case AstalNetwork.Primary.WIRED:
                self._network_binding = nw.get_wired().bind_property(
                    "icon-name",
                    self,
                    "network-icon",
                    SYNC,
                )
                return nw.get_wired().get_icon_name()
            case AstalNetwork.Primary.WIFI:
                self._network_binding = nw.get_wifi().bind_property(
                    "icon-name",
                    self,
                    "network-icon",
                    SYNC,
                )
                return nw.get_wifi().get_icon_name()
            case _:
                return "network-idle-symbolic"

    def set_clock(self):
        self.clock = GLib.DateTime.new_now_local().format("%H:%M")

    @Gtk.Template.Callback()
    def menu_clicked(self, _) -> None:
        if self.window_manager:
            self.window_manager.toggle_menu(self.get_monitor())