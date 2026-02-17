from gi.repository import Astal, Gtk
from ui.common.PopupWindow import PopupWindow
from utils import Blueprint
from .DeviceMenu import DeviceMenu

@Blueprint("quicksettings/DeviceMenuWindow.blp")
class DeviceMenuWindow(Astal.Window, PopupWindow):
    __gtype_name__ = 'DeviceMenuWindow'

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.setup_popup()
