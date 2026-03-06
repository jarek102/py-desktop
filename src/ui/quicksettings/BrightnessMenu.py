import versions
from gi.repository import Gtk, GObject
from services.BrightnessService import BrightnessService
from ui.quicksettings.BrightnessItem import BrightnessItem
from ui.common.PanelRow import PanelRow

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL


class BrightnessMenu(PanelRow):
    __gtype_name__ = "BrightnessMenu"

    value = GObject.Property(type=float, default=0.0)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.icon_name = "display-brightness-symbolic"
        self.icon_sensitive = False
        self.set_has_revealer(True)
        slider_adjustment = Gtk.Adjustment(
            lower=0,
            upper=100,
            step_increment=10,
            page_increment=10,
            value=0.0,
        )
        self._slider = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            hexpand=True,
            valign=Gtk.Align.CENTER,
            draw_value=False,
            adjustment=slider_adjustment,
        )
        for mark_value in [0, 1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            self._slider.add_mark(mark_value, Gtk.PositionType.BOTTOM, None)
        self._slider.bind_property("value", self, "value", BIDI | SYNC)
        self.set_content_widget(self._slider)

        self.service = BrightnessService()
        self.service.bind_property("brightness", self, "value", BIDI | SYNC)

        if self.service.initialization_task:
            self.service.initialization_task.add_done_callback(
                self._on_initialized
            )

    def _on_initialized(self, _task) -> None:
        for monitor in self.service.monitors:
            self.add_revealer_child(BrightnessItem(monitor))
