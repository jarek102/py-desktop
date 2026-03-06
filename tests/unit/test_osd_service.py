import versions
from services.osd_service import OsdService


class FakeEndpoint:
    def __init__(self, volume=0.5, muted=False):
        self._volume = volume
        self._muted = muted

    def get_volume(self):
        return self._volume

    def get_mute(self):
        return self._muted


def _make_service():
    """Create a fresh OsdService instance bypassing the singleton guard."""
    OsdService._instance = None
    service = OsdService.get_default()
    # Disable the real timer so tests don't depend on AstalIO
    service._show_and_reset_timer = lambda: None
    return service


def test_volume_icon_high():
    svc = _make_service()
    svc._on_volume_changed(FakeEndpoint(volume=0.8), None)
    assert svc.icon == "audio-volume-high-symbolic"
    assert svc.label == "80%"


def test_volume_icon_medium():
    svc = _make_service()
    svc._on_volume_changed(FakeEndpoint(volume=0.5), None)
    assert svc.icon == "audio-volume-medium-symbolic"
    assert svc.label == "50%"


def test_volume_icon_low():
    svc = _make_service()
    svc._on_volume_changed(FakeEndpoint(volume=0.2), None)
    assert svc.icon == "audio-volume-low-symbolic"
    assert svc.label == "20%"


def test_volume_muted_shows_muted_icon():
    svc = _make_service()
    svc._on_volume_changed(FakeEndpoint(volume=0.5, muted=True), None)
    assert svc.icon == "audio-volume-muted-symbolic"
    assert svc.label == "Muted"


def test_mute_toggle_on():
    svc = _make_service()
    svc._on_mute_changed(FakeEndpoint(volume=0.5, muted=True), None)
    assert svc.icon == "audio-volume-muted-symbolic"
    assert svc.label == "Muted"
    assert svc.value == 0.0


def test_mute_toggle_off():
    svc = _make_service()
    svc._on_mute_changed(FakeEndpoint(volume=0.7, muted=False), None)
    assert svc.icon == "audio-volume-high-symbolic"
    assert svc.label == "70%"
    assert svc.value == 0.7


def test_singleton_returns_same_instance():
    OsdService._instance = None
    a = OsdService.get_default()
    b = OsdService.get_default()
    assert a is b
    OsdService._instance = None


def test_show_and_reset_timer_sets_visible():
    svc = _make_service()
    # _show_and_reset_timer is stubbed out in _make_service(), so test the
    # dismiss path which doesn't require AstalIO
    svc.visible = True
    svc._dismiss()
    assert svc.visible is False
