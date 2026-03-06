import gi
from gi.repository import Gtk, GObject, AstalWp as Wp
from ui.quicksettings.AudioItem import AudioItem
from ui.common.PanelRow import PanelRow
from utils import Blueprint

SYNC = GObject.BindingFlags.SYNC_CREATE
BIDI = GObject.BindingFlags.BIDIRECTIONAL


def _is_disconnected_display_sink(endpoint: Wp.Endpoint) -> bool:
    """Filter out GPU display audio sinks whose display is disconnected.

    ProAudio GPU sinks (node.name contains '.pro-output-') that lack an
    object.path are bridge nodes created for disconnected HDMI/DP ports.
    Connected display sinks get a real ALSA PCM node with object.path set.
    """
    node_name = endpoint.get_pw_property("node.name") or ""
    if ".pro-output-" not in node_name:
        return False
    return not endpoint.get_pw_property("object.path")


@Blueprint("quicksettings/VolumeMenu.blp")
class VolumeMenu(Gtk.Box):
    __gtype_name__ = 'VolumeMenu'

    panel_row = Gtk.Template.Child()

    icon_name           = GObject.Property(type=str)
    value               = GObject.Property(type=float)
    active_device_label = GObject.Property(type=str, default="")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.wp = Wp.get_default()
        self.audio = self.wp.get_audio()
        self.endpoint = None
        self._bindings = []
        self.type = None

        # Build slider imperatively (do_add_child slot mechanism unavailable in PyGObject)
        self._vol_adj = Gtk.Adjustment(lower=0, upper=1.0, value=0.0)
        slider = Gtk.Scale(adjustment=self._vol_adj, draw_value=False, hexpand=True, valign=Gtk.Align.CENTER)
        self.panel_row.set_content_widget(slider)

        # Chain: adjustment.value ↔ self.value ↔ endpoint.volume (set in bind_default)
        self._vol_adj.bind_property("value", self, "value", BIDI | SYNC)

        self.panel_row.connect("icon-activated", self._on_icon_activated)
        self.panel_row.connect("chevron-activated", self._on_chevron)

    def setup(self, type: str) -> None:
        self.type = type
        if type == "speaker":
            self.wp.connect("notify::default-speaker", self.on_default_changed)
            self.audio.connect("speaker-added", self.refresh_items)
            self.audio.connect("speaker-removed", self.refresh_items)
        elif type == "microphone":
            self.wp.connect("notify::default-microphone", self.on_default_changed)
            self.audio.connect("microphone-added", self.refresh_items)
            self.audio.connect("microphone-removed", self.refresh_items)

        self.bind_default()
        self.refresh_items()

    def bind_default(self) -> None:
        for binding in self._bindings:
            binding.unbind()
        self._bindings.clear()

        if self.type == "speaker":
            self.endpoint = self.wp.get_default_speaker()
        else:
            self.endpoint = self.wp.get_default_microphone()

        if self.endpoint:
            self._bindings = [
                self.endpoint.bind_property("volume-icon", self, "icon_name", SYNC),
                self.endpoint.bind_property("volume", self, "value", BIDI | SYNC),
                self.endpoint.bind_property("description", self, "active_device_label", SYNC),
            ]

    def on_default_changed(self, *args) -> None:
        self.bind_default()

    def refresh_items(self, *args) -> None:
        box = self.panel_row.revealer_box
        child = box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            box.remove(child)
            child = next_child

        items = (
            self.audio.get_speakers()
            if self.type == "speaker"
            else self.audio.get_microphones()
        )
        if items:
            for item in items:
                box.append(AudioItem(item))

    def _on_icon_activated(self, _panel_row: PanelRow) -> None:
        if self.endpoint:
            self.endpoint.set_mute(not self.endpoint.get_mute())

    def _on_chevron(self, _panel_row: PanelRow) -> None:
        # PanelRow handles the reveal toggle internally; nothing extra needed
        pass
