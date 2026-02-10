import logging
import subprocess
import versions
from gi.repository import Gtk
from utils import Blueprint

logger = logging.getLogger(__name__)

@Blueprint("bar/Launcher.blp")
class Launcher(Gtk.Button):
    __gtype_name__ = "Launcher"

    def __init__(self):
        super().__init__()

    @Gtk.Template.Callback()
    def on_clicked(self, _button: Gtk.Button) -> None:
        try:
            subprocess.Popen(
                ["wofi", "--show", "drun", "--allow-images", "--columns", "3", "--gtk-dark"]
            )
        except Exception as error:
            logger.error(f"Failed to launch wofi: {error}")