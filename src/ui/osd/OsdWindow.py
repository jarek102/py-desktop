import versions
from gi.repository import Astal, Gtk, GObject

from services.osd_service import OsdService
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE


@Blueprint("osd/OsdWindow.blp")
class OsdWindow(Astal.Window):
    __gtype_name__ = "OsdWindow"

    icon = GObject.Property(type=str, default="")
    value = GObject.Property(type=float, default=0.0)
    label = GObject.Property(type=str, default="")

    level_bar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = OsdService.get_default()
        self._service.bind_property("icon", self, "icon", SYNC)
        self._service.bind_property("value", self, "value", SYNC)
        self._service.bind_property("label", self, "label", SYNC)
        self._service.connect("notify::visible", self._on_visibility_changed)
        self.hide()  # start hidden; shown only when service triggers

    def _on_visibility_changed(self, service, _pspec):
        if service.visible:
            self.present()
        else:
            self.hide()
