import logging
import versions
from gi.repository import GObject, AstalIO, AstalWp as Wp

_log = logging.getLogger("py_desktop.osd")

DISMISS_MS = 1500


class OsdService(GObject.Object):
    """Singleton that collects OSD triggers (volume, mute, and optionally brightness)
    and exposes unified state for the OSD window to bind to."""

    __gtype_name__ = "OsdService"

    _instance = None

    icon = GObject.Property(type=str, default="")
    value = GObject.Property(type=float, default=0.0)
    label = GObject.Property(type=str, default="")
    visible = GObject.Property(type=bool, default=False)

    @classmethod
    def get_default(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, **kwargs):
        if OsdService._instance is not None:
            raise RuntimeError("Use OsdService.get_default()")
        super().__init__(**kwargs)
        self._timer = None
        self._wp = None
        self._audio = None
        self._endpoint = None
        self._endpoint_bindings_ids: list[int] = []
        self._brightness_service = None
        self._ready = False

    def start(self, brightness_service=None):
        """Connect to audio (and optionally brightness) sources. Call once after services are available."""
        if self._ready:
            return
        self._ready = True

        # Audio (volume + mute)
        self._wp = Wp.get_default()
        self._audio = self._wp.get_audio()  # type: ignore[reportOptionalMemberAccess]
        self._wp.connect("notify::default-speaker", self._on_default_speaker_changed)
        self._bind_speaker()

        # Brightness
        if brightness_service is not None:
            self._brightness_service = brightness_service
            self._brightness_service.connect("notify::brightness", self._on_brightness_changed)

    def _bind_speaker(self):
        """Rebind to current default speaker endpoint."""
        # Disconnect old signal handlers
        if self._endpoint is not None:
            for handler_id in self._endpoint_bindings_ids:
                self._endpoint.disconnect(handler_id)
        self._endpoint_bindings_ids.clear()

        self._endpoint = self._wp.get_default_speaker()  # type: ignore[reportOptionalMemberAccess]
        if self._endpoint is not None:
            self._endpoint_bindings_ids = [
                self._endpoint.connect("notify::volume", self._on_volume_changed),
                self._endpoint.connect("notify::mute", self._on_mute_changed),
            ]

    def _on_default_speaker_changed(self, *_args):
        self._bind_speaker()

    @staticmethod
    def _icon_for_volume(volume: float, muted: bool) -> str:
        if muted:
            return "audio-volume-muted-symbolic"
        percent = round(volume * 100)
        if percent > 66:
            return "audio-volume-high-symbolic"
        elif percent > 33:
            return "audio-volume-medium-symbolic"
        return "audio-volume-low-symbolic"

    def _on_volume_changed(self, endpoint, _pspec):
        volume = endpoint.get_volume()
        muted = endpoint.get_mute()
        percent = round(volume * 100)

        self.icon = self._icon_for_volume(volume, muted)
        self.label = "Muted" if muted else f"{percent}%"
        self.value = volume
        self._show_and_reset_timer()

    def _on_mute_changed(self, endpoint, _pspec):
        muted = endpoint.get_mute()
        volume = endpoint.get_volume()

        self.icon = self._icon_for_volume(volume, muted)
        self.label = "Muted" if muted else f"{round(volume * 100)}%"
        self.value = 0.0 if muted else volume
        self._show_and_reset_timer()

    def _on_brightness_changed(self, service, _pspec):
        if service.busy:
            # Suppress the initial read emitted during initialize()
            return
        brightness = service.get_property("brightness")
        percent = round(brightness)

        self.icon = "display-brightness-symbolic"
        self.value = brightness / 100.0
        self.label = f"{percent}%"
        self._show_and_reset_timer()

    def _show_and_reset_timer(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

        self.visible = True
        self._timer = AstalIO.Time.timeout(DISMISS_MS, self._dismiss)  # type: ignore[reportAttributeAccessIssue]

    def _dismiss(self, *_args):
        self.visible = False
        self._timer = None
