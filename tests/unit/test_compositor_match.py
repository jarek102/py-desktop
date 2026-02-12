from services.compositor_match import MonitorTarget, workspace_matches_monitor


class DummyMonitor:
    def __init__(self, *, name=None, gdk_id=None, gdk_monitor=None):
        self.name = name
        self.gdk_id = gdk_id
        self.gdk_monitor = gdk_monitor


def test_matches_by_gdk_monitor():
    shared_gdk_monitor = object()
    workspace_monitor = DummyMonitor(gdk_monitor=shared_gdk_monitor)
    target = MonitorTarget(gdk_monitor=shared_gdk_monitor)

    assert workspace_matches_monitor(workspace_monitor, target) is True


def test_matches_by_gdk_id():
    workspace_monitor = DummyMonitor(gdk_id=2)
    target = MonitorTarget(gdk_id=2)

    assert workspace_matches_monitor(workspace_monitor, target) is True


def test_matches_by_name_fallback():
    workspace_monitor = DummyMonitor(name="DP-1")
    target_monitor = DummyMonitor(name="DP-1")
    target = MonitorTarget(monitor=target_monitor)

    assert workspace_matches_monitor(workspace_monitor, target) is True


def test_returns_false_for_none_workspace_monitor():
    target = MonitorTarget(gdk_id=0)

    assert workspace_matches_monitor(None, target) is False


def test_gdk_monitor_match_has_priority_over_other_fields():
    workspace_monitor = DummyMonitor(gdk_monitor="A", gdk_id=7, name="DP-1")
    target = MonitorTarget(gdk_monitor="B", gdk_id=7, monitor=DummyMonitor(name="DP-1"))

    assert workspace_matches_monitor(workspace_monitor, target) is False
