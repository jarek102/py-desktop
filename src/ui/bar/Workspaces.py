import logging
import versions
from gi.repository import Gtk, GObject, Gdk
from utils import Blueprint
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
        
        self.connect("clicked", self.on_clicked)
        
        # Listen for active state changes (specifically for Niri)
        self.workspace.connect("notify::is-active", self._update_state)
        self._update_state()
        _log.info("WorkspaceButton init id=%s name=%s", self.id, self.name)

    def on_clicked(self, _):
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
        self.compositor.connect("workspaces-changed", self.on_workspaces_changed)
        
        # Scroll to switch workspaces
        scroll = Gtk.EventControllerScroll(flags=Gtk.EventControllerScrollFlags.VERTICAL)
        scroll.connect("scroll", self.on_scroll)
        self.add_controller(scroll)
        
        # Defer initial load until widget is mapped, so we can get the monitor
        self.connect("map", self._on_map)

    def _on_map(self, *args):
        # Run once
        self.disconnect_by_func(self._on_map)
        self.on_workspaces_changed()

    def on_workspaces_changed(self, *args):
        root = self.get_root()

        gdk_monitor_id = root.get_monitor()
        _log.info("Workspaces changed gdk_monitor_id=%s", gdk_monitor_id)

        # Clear existing children
        while child := self.get_first_child():
            self.remove(child)
        
        workspaces_to_show = self.compositor.get_workspaces_for_monitor(gdk_id=gdk_monitor_id)
        _log.info("Workspaces to show count=%s ids=%s", len(workspaces_to_show), [w.id for w in workspaces_to_show])
            
        for ws in workspaces_to_show:
            self.append(WorkspaceButton(ws))
        
        child = self.get_first_child()
        while child:
            if isinstance(child, WorkspaceButton):
                child._update_state()
            child = child.get_next_sibling()

    def on_scroll(self, controller, dx, dy):
        _log.info("Workspaces scroll dx=%s dy=%s", dx, dy)
        children = []
        child = self.get_first_child()
        while child:
            if isinstance(child, WorkspaceButton):
                children.append(child)
            child = child.get_next_sibling()
            
        if not children:
            _log.info("Workspaces scroll ignored: no children")
            return

        active_index = -1
        for i, btn in enumerate(children):
            if btn.has_css_class("active"):
                active_index = i
                break
        _log.info("Workspaces scroll active_index=%s total=%s", active_index, len(children))
        
        target_index = active_index
        if dy > 0: target_index += 1
        elif dy < 0: target_index -= 1
        _log.info("Workspaces scroll target_index=%s", target_index)
        
        if 0 <= target_index < len(children):
            target = children[target_index]
            _log.info("Workspaces scroll focus id=%s name=%s", target.id, target.name)
            children[target_index].workspace.focus()
