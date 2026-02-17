from gi.repository import (
    Astal,
    GObject,
    Gtk,
)

from ui.common.FeatureToggle import FeatureToggle
from ui.quicksettings.BrightnessMenu import BrightnessMenu
from ui.quicksettings.VolumeMenu import VolumeMenu
from ui.quicksettings.BluetoothMenu import BluetoothMenu
from ui.common.PopupWindow import PopupWindow
from utils import Blueprint
from services.Compositor import Compositor
from services import system_actions
from services.theme_service import ThemeService
from services.power_profile_service import PowerProfileService

@Blueprint("quicksettings/DeviceMenu.blp")
class DeviceMenu(Gtk.Box):
    __gtype_name__ = 'DeviceMenu'

    is_dark_mode = GObject.Property(type=bool, default=False)
    power_profiles_visible = GObject.Property(type=bool, default=False)
    power_saver_active = GObject.Property(type=bool, default=False)
    balanced_active = GObject.Property(type=bool, default=True)
    performance_active = GObject.Property(type=bool, default=False)
    
    audio_menu = Gtk.Template.Child()
    mic_menu = Gtk.Template.Child()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


        self.theme_service = ThemeService()
        self.power_profile_service = PowerProfileService()

        # Bind theme properties directly
        self.theme_service.bind_property(
            "is_dark", self, "is_dark_mode", GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL
        )
        
        # Determine initial state
        self.is_dark_mode = self.theme_service.is_dark

        # Bind power profile visibility
        self.power_profile_service.bind_property(
            "visible", self, "power_profiles_visible", GObject.BindingFlags.SYNC_CREATE
        )

        self.power_profile_service.connect(
            "notify::active-profile", self._on_power_profile_changed
        )
        self._on_power_profile_changed()
        
        self.audio_menu.setup("speaker")
        self.mic_menu.setup("microphone")

    def _on_power_profile_changed(self, *_args):
        active = self.power_profile_service.active_profile
        self.power_saver_active = active == "power-saver"
        self.balanced_active = active == "balanced"
        self.performance_active = active == "performance"

    @Gtk.Template.Callback()
    def logout_clicked(self, _) -> None:
        Compositor.get_default().logout()

    @Gtk.Template.Callback()
    def power_saver_clicked(self, button) -> None:
        if button.get_active():
            self.power_profile_service.set_profile("power-saver")

    @Gtk.Template.Callback()
    def balanced_clicked(self, button) -> None:
        if button.get_active():
            self.power_profile_service.set_profile("balanced")

    @Gtk.Template.Callback()
    def performance_clicked(self, button) -> None:
        if button.get_active():
            self.power_profile_service.set_profile("performance")
        
    @Gtk.Template.Callback()
    def reboot_clicked(self, _) -> None:
        system_actions.reboot()
        
    @Gtk.Template.Callback()
    def poweroff_clicked(self, _) -> None:
        system_actions.poweroff()

    @Gtk.Template.Callback()
    def sleep_clicked(self, _) -> None:
        system_actions.suspend()
