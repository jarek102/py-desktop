import pathlib
import subprocess
import gi

from gi.repository import (
    Gio, 
    Gtk,
    GObject,
    Astal,
    AstalWp as Wp,
    AstalHyprland as Hyprland,
)

from ui.BrightnessService import BrightnessService
from ui.BluetoothMenu import BluetoothMenu

BASE_DIR = pathlib.Path(__file__).resolve().parent
UI_FILE = BASE_DIR / 'DeviceMenu.ui'

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL

@Gtk.Template(filename=UI_FILE.as_posix())
class DeviceMenu(Astal.Window):
    __gtype_name__ = 'DeviceMenu'
    
    brightness = GObject.Property(type=int)
    volume = GObject.Property(type=float)
    volume_icon = GObject.Property(type=str)

    def __init__(self, **kwargs) -> None:
        super().__init__(
            anchor=Astal.WindowAnchor.RIGHT
            | Astal.WindowAnchor.TOP, # pyright: ignore[reportOperatorIssue]
            exclusivity=Astal.Exclusivity.EXCLUSIVE,
            **kwargs)
        
        self.brightness_service = BrightnessService()
        self.brightness_service.bind_property("brightness",self,"brightness", SYNC)
        
        speaker = Wp.get_default().get_audio().get_default_speaker()
        speaker.bind_property("volume-icon", self, "volume-icon", SYNC)
        speaker.bind_property("volume", self, "volume", SYNC)
        self.connect('notify::volume_icon', lambda self: print(self.volume_icon))

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
    def change_brightness(self, scale, _type, value) -> None:
        value = int(round(value,-1))
        self.brightness_service.brightness = value
