from services.Compositor import Compositor


class DummyScroll:
    def __init__(self):
        self.stop_called = False
        self.quit_called = False

    def stop_event_monitor(self):
        self.stop_called = True

    def quit(self):
        self.quit_called = True
        return True


def test_logout_scroll_stops_monitor_and_quits():
    compositor = Compositor.__new__(Compositor)
    compositor._desktop = "scroll"
    compositor._hyprland = None
    compositor._niri = None
    compositor._scroll = DummyScroll()

    Compositor.logout(compositor)

    assert compositor._scroll.stop_called is True
    assert compositor._scroll.quit_called is True
