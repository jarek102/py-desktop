import pathlib
import subprocess
import gi

from gi.repository import (
    Astal,
    Gtk,
    GObject,
    AstalWp as Wp,
    AstalHyprland as Hyprland,
)

from ui.BrightnessService import BrightnessService
from ui.BluetoothMenu import BluetoothMenu
from ui.PopupWindow import PopupWindow

BASE_DIR = pathlib.Path(__file__).resolve().parent
UI_FILE = BASE_DIR / 'DeviceMenu.ui'

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL

@Gtk.Template(filename=UI_FILE.as_posix())
class DeviceMenu(Astal.Window, PopupWindow):
    __gtype_name__ = 'DeviceMenu'
    
    brightness_scale = Gtk.Template.Child()
    brightness = GObject.Property(type=int)
    volume = GObject.Property(type=float)
    volume_icon = GObject.Property(type=str)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.setup_popup()
        
        self.brightness_service = BrightnessService()
        self.brightness_service.bind_property("brightness",self,"brightness", SYNC)
        
        speaker = Wp.get_default().get_default_speaker()
        speaker.bind_property("volume-icon", self, "volume-icon", SYNC)
        speaker.bind_property("volume", self, "volume", SYNC)

    @Gtk.Template.Callback()
    def close_clicked(self, _) -> None:
        self.hide()

    @Gtk.Template.Callback()
    def logout_clicked(self, _) -> None:
        Hyprland.get_default().dispatch("exit","")
        
    @Gtk.Template.Callback()
    def reboot_clicked(self, _) -> None:
        subprocess.Popen(["systemctl", "reboot"])
        
    @Gtk.Template.Callback()
    def poweroff_clicked(self, _) -> None:
        subprocess.Popen(["systemctl", "poweroff"])
        
    @Gtk.Template.Callback()
    def change_volume(self, _scale, _type, value) -> None:
        Wp.get_default().get_default_speaker().set_volume(value)
        
    @Gtk.Template.Callback()
    def change_brightness(self, scale, _type, value) -> bool:
        snapped_value = int(round(value / 10) * 10)
        self.brightness_service.brightness = snapped_value
        scale.set_value(snapped_value)
        return True
