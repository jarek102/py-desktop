from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MonitorTarget:
    monitor: Any = None
    gdk_id: int | None = None
    gdk_monitor: Any = None


def workspace_matches_monitor(workspace_monitor: Any, target: MonitorTarget) -> bool:
    if workspace_monitor is None:
        return False

    if target.gdk_monitor is not None:
        return getattr(workspace_monitor, "gdk_monitor", None) == target.gdk_monitor

    if target.gdk_id is not None:
        return getattr(workspace_monitor, "gdk_id", None) == target.gdk_id

    monitor = target.monitor
    if monitor is None:
        return False

    target_gdk_monitor = getattr(monitor, "gdk_monitor", None)
    workspace_gdk_monitor = getattr(workspace_monitor, "gdk_monitor", None)
    if target_gdk_monitor is not None and workspace_gdk_monitor is not None:
        return workspace_gdk_monitor == target_gdk_monitor

    target_gdk_id = getattr(monitor, "gdk_id", None)
    workspace_gdk_id = getattr(workspace_monitor, "gdk_id", None)
    if target_gdk_id is not None and workspace_gdk_id is not None:
        return workspace_gdk_id == target_gdk_id

    target_name = getattr(monitor, "name", None)
    workspace_name = getattr(workspace_monitor, "name", None)
    if target_name and workspace_name:
        return workspace_name == target_name

    return False
