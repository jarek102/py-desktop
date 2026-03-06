import logging
from gi.repository import Gtk, GObject
from services.BrightnessService import BrightnessService
from ui.quicksettings.BrightnessItem import BrightnessItem
from ui.common.PanelRow import PanelRow
from utils import Blueprint

_log = logging.getLogger("py_desktop.brightness_menu")

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL


@Blueprint("quicksettings/BrightnessMenu.blp")
class BrightnessMenu(Gtk.Box):
    __gtype_name__ = "BrightnessMenu"

    panel_row = Gtk.Template.Child()

    value = GObject.Property(type=float, default=0.0)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = BrightnessService.get_default()

        # Build slider imperatively (do_add_child slot mechanism unavailable in PyGObject)
        self._brightness_adj = Gtk.Adjustment(lower=0, upper=100, step_increment=10, page_increment=10, value=0.0)
        slider = Gtk.Scale(adjustment=self._brightness_adj, draw_value=False, hexpand=True, valign=Gtk.Align.CENTER)
        for mark_val in range(0, 101, 10):
            slider.add_mark(mark_val, Gtk.PositionType.BOTTOM, None)
        self.panel_row.set_content_widget(slider)

        # Chain: adjustment.value ↔ self.value ↔ service.brightness
        self._brightness_adj.bind_property("value", self, "value", BIDI | SYNC)
        self.service.bind_property("brightness", self, "value", BIDI | SYNC)

        self.panel_row.connect("chevron-activated", self._on_chevron)

        if self.service.initialization_task:
            self.service.initialization_task.add_done_callback(self._on_initialized)

    def _on_initialized(self, _task) -> None:
        for monitor in self.service.monitors:
            item = BrightnessItem(monitor)
            self.panel_row.revealer_box.append(item)
        # Show chevron only when there are multiple monitors
        self.panel_row.chevron_visible = len(self.service.monitors) > 1

    def _on_chevron(self, _panel_row: PanelRow) -> None:
        # PanelRow handles the reveal toggle internally; nothing extra needed
        pass
