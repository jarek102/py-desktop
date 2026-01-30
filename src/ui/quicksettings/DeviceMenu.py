import subprocess
import gi

from gi.repository import (
    Astal,
    Gtk,
    GObject,
    AstalWp as Wp,
    AstalHyprland as Hyprland,
)

from ui.quicksettings.BrightnessMenu import BrightnessMenu
from ui.quicksettings.VolumeMenu import VolumeMenu
from ui.quicksettings.BluetoothMenu import BluetoothMenu
from ui.common.PopupWindow import PopupWindow
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL

@Blueprint("quicksettings/DeviceMenu.blp")
class DeviceMenu(Astal.Window, PopupWindow):
    __gtype_name__ = 'DeviceMenu'
    
    audio_menu = Gtk.Template.Child()
    mic_menu = Gtk.Template.Child()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.setup_popup()
        
        self.audio_menu.setup("speaker")
        self.mic_menu.setup("microphone")

    @Gtk.Template.Callback()
    def logout_clicked(self, _) -> None:
        Hyprland.get_default().dispatch("exit","")
        
    @Gtk.Template.Callback()
    def reboot_clicked(self, _) -> None:
        subprocess.Popen(["systemctl", "reboot"])
        
    @Gtk.Template.Callback()
    def poweroff_clicked(self, _) -> None:
        subprocess.Popen(["systemctl", "poweroff"])
