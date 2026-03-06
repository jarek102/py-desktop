import versions
from gi.repository import Gtk, GObject, AstalWp as Wp
from ui.quicksettings.AudioItem import AudioItem
from ui.common.PanelRow import PanelRow

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


class VolumeMenu(PanelRow):
    __gtype_name__ = "VolumeMenu"

    node_type = GObject.Property(type=str, default="")
    value = GObject.Property(type=float, default=0.0)
    active_device_label = GObject.Property(type=str, default="")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.wp = Wp.get_default()
        self.audio = self.wp.get_audio()
        self.endpoint = None
        self._bindings: list = []
        self._node_type_value: str = ""
        self._is_setup: bool = False

        slider_adjustment = Gtk.Adjustment(lower=0, upper=1.0, value=0.0)
        self._slider = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            hexpand=True,
            valign=Gtk.Align.CENTER,
            draw_value=False,
            adjustment=slider_adjustment,
        )
        self._slider.bind_property("value", self, "value", BIDI | SYNC)
        self.set_content_widget(self._slider)
        self.set_has_revealer(True)

        # Caption shows active device name when revealer is collapsed
        self.bind_property("active_device_label", self, "caption", SYNC)
        self.caption_visible = True

        self.connect("notify::node-type", self._on_node_type_changed)

    def _on_node_type_changed(self, *_args) -> None:
        node_type = self.get_property("node-type")
        if node_type and not self._is_setup:
            self._setup(node_type)

    def _setup(self, node_type: str) -> None:
        self._node_type_value = node_type
        self._is_setup = True

        if node_type == "speaker":
            self.icon_name = "audio-volume-high-symbolic"
            self.wp.connect("notify::default-speaker", self._on_default_changed)
            self.audio.connect("speaker-added", self._refresh_items)
            self.audio.connect("speaker-removed", self._refresh_items)
        elif node_type == "microphone":
            self.icon_name = "microphone-sensitivity-high-symbolic"
            self.wp.connect("notify::default-microphone", self._on_default_changed)
            self.audio.connect("microphone-added", self._refresh_items)
            self.audio.connect("microphone-removed", self._refresh_items)

        self._bind_default()
        self._refresh_items()

    def setup(self, node_type: str) -> None:
        # Compatibility path while DeviceMenu still calls setup().
        if self._is_setup:
            return
        self.set_property("node-type", node_type)

    def _bind_default(self) -> None:
        for binding in self._bindings:
            binding.unbind()
        self._bindings.clear()

        if self._node_type_value == "speaker":
            self.endpoint = self.wp.get_default_speaker()
        else:
            self.endpoint = self.wp.get_default_microphone()

        if self.endpoint:
            self._bindings = [
                self.endpoint.bind_property("volume-icon", self, "icon_name", SYNC),
                self.endpoint.bind_property("volume", self, "value", BIDI | SYNC),
                self.endpoint.bind_property(
                    "description", self, "active_device_label", SYNC
                ),
            ]

    def bind_default(self) -> None:
        self._bind_default()

    def _on_default_changed(self, *_args) -> None:
        self._bind_default()

    def on_default_changed(self, *_args) -> None:
        # Backward compatibility for existing unit test entrypoint.
        if hasattr(self, "bind_default"):
            self.bind_default()
        else:
            self._on_default_changed(*_args)

    def _refresh_items(self, *_args) -> None:
        child = self.revealer_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.revealer_box.remove(child)
            child = next_child

        if self._node_type_value == "speaker":
            items = [
                item for item in self.audio.get_speakers()
                if not _is_disconnected_display_sink(item)
            ]
        else:
            items = self.audio.get_microphones()

        for item in items:
            self.revealer_box.append(AudioItem(item))

    def refresh_items(self, *_args) -> None:
        self._refresh_items(*_args)

    def on_icon_clicked(self, _button: Gtk.Button) -> None:
        if self.endpoint:
            self.endpoint.set_mute(not self.endpoint.get_mute())

    def on_toggle_clicked(self, _button: Gtk.ToggleButton) -> None:
        pass  # VolumeMenu has no toggle button
