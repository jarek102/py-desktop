import logging
import versions
from gi.repository import Gtk, GObject, Gdk
from utils import Blueprint, ScrollThrottle
from services.Compositor import Compositor

_log = logging.getLogger("py_desktop.workspaces")
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

@Blueprint("bar/WorkspaceButton.blp")
class WorkspaceButton(Gtk.Button):
    __gtype_name__ = "WorkspaceButton"
    
    id = GObject.Property(type=int, default=0)
    name = GObject.Property(type=str, default="")
    id_string = GObject.Property(type=str, default="")


    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace
        workspace.bind_property("id", self, "id", GObject.BindingFlags.SYNC_CREATE)
        workspace.bind_property(
            "id",
            self,
            "id_string",
            GObject.BindingFlags.SYNC_CREATE,
            lambda _binding, value: (True, str(value) if value is not None else ""),
        )
        workspace.bind_property("name", self, "name", GObject.BindingFlags.SYNC_CREATE)
        workspace.bind_property(
            "name",
            self,
            "tooltip_text",
            GObject.BindingFlags.SYNC_CREATE,
            lambda _binding, value: (True, str(value) if value is not None else ""),
        )
        
        self.connect("clicked", self._on_clicked)
        
        # Listen for active state changes (specifically for Niri)
        self.workspace.connect("notify::is-active", self._update_state)
        self._update_state()
    def _on_clicked(self, _):
        _log.info("WorkspaceButton clicked id=%s name=%s", self.id, self.name)
        self.workspace.focus()
        
    def _update_state(self, *args):
        is_active = self.workspace.get_property("is-active")
        _log.debug("WorkspaceButton state id=%s active=%s", self.id, is_active)
        if is_active:
            self.add_css_class("active")
        else:
            self.remove_css_class("active")

@Blueprint("bar/Workspaces.blp")
class Workspaces(Gtk.Box):
    __gtype_name__ = "Workspaces"

    def __init__(self):
        super().__init__()
        self.compositor = Compositor.get_default()
        self._scroll_throttle = ScrollThrottle(threshold=1.0)
        self.compositor.connect("workspaces-changed", self.on_workspaces_changed)
        
        # Scroll to switch workspaces
        scroll_controller = Gtk.EventControllerScroll(
            flags=(
                Gtk.EventControllerScrollFlags.VERTICAL
                | Gtk.EventControllerScrollFlags.DISCRETE
            )
        )
        scroll_controller.connect("scroll", self._on_scroll)
        self.add_controller(scroll_controller)
        
        # Defer initial load until widget is mapped, so we can get the monitor
        self.connect("map", self._on_map)

    def _on_map(self, *args):
        # Run once
        self.disconnect_by_func(self._on_map)
        self.on_workspaces_changed()

    def on_workspaces_changed(self, *args):
        root = self.get_root()
        if root is None:
            _log.debug("Workspaces update skipped: widget root is not available yet")
            return
        if not hasattr(root, "get_monitor"):
            _log.warning("Workspaces update skipped: root has no get_monitor()")
            return

        gdk_monitor_id = root.get_monitor()
        _log.debug("Workspaces changed gdk_monitor_id=%s", gdk_monitor_id)

        # Clear existing children
        while child := self.get_first_child():
            self.remove(child)
        
        workspaces_to_show = self.compositor.get_workspaces_for_monitor(gdk_id=gdk_monitor_id)
        _log.debug("Workspaces to show count=%s ids=%s", len(workspaces_to_show), [w.id for w in workspaces_to_show])
            
        for ws in workspaces_to_show:
            self.append(WorkspaceButton(ws))
        
        child = self.get_first_child()
        while child:
            if isinstance(child, WorkspaceButton):
                child._update_state()
            child = child.get_next_sibling()
        self._scroll_throttle.reset()

    def _on_scroll(self, _controller, _dx: float, dy: float) -> None:
        steps = self._scroll_throttle.feed(dy)
        if steps == 0:
            return

        _log.debug("Workspaces scroll steps=%s", steps)

        root = self.get_root()
        if root is None or not hasattr(root, "get_monitor"):
            return

        workspaces = self.compositor.get_workspaces_for_monitor(
            gdk_id=root.get_monitor()
        )
        if not workspaces:
            return

        # Use model state — do NOT use CSS class to find active workspace.
        focused_index = next(
            (i for i, ws in enumerate(workspaces) if ws.get_property("is-focused")),
            None,
        )
        if focused_index is None:
            # Fallback: use is-active if no workspace reports is-focused.
            focused_index = next(
                (
                    i
                    for i, ws in enumerate(workspaces)
                    if ws.get_property("is-active")
                ),
                0,
            )

        target_index = max(0, min(focused_index + steps, len(workspaces) - 1))

        if target_index != focused_index:
            _log.debug(
                "Workspaces scroll: focusing index=%s id=%s",
                target_index,
                workspaces[target_index].id,
            )
            workspaces[target_index].focus()
