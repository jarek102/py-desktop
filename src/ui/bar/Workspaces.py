import versions
from gi.repository import Gtk, GObject, Gdk
from utils import Blueprint
from services.Compositor import Compositor

@Blueprint("bar/WorkspaceButton.blp")
class WorkspaceButton(Gtk.Button):
    __gtype_name__ = "WorkspaceButton"
    
    id = GObject.Property(type=int)
    name = GObject.Property(type=str)


    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace
        workspace.bind_property("id", self, "id", GObject.BindingFlags.SYNC_CREATE)
        workspace.bind_property("name", self, "name", GObject.BindingFlags.SYNC_CREATE)
        workspace.bind_property("name", self, "tooltip_text", GObject.BindingFlags.SYNC_CREATE)
        
        self.connect("clicked", self.on_clicked)
        
        # Listen for active state changes (specifically for Niri)
        self.workspace.connect("notify::is-active", self._update_state)
        self._update_state()

    def on_clicked(self, _):
        self.workspace.focus()
        
    def _update_state(self, *args):
        is_active = self.workspace.get_property("is-active")
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
        self.compositor.connect("focused-workspace-changed", self.on_focused_changed)
        
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

        # Clear existing children
        while child := self.get_first_child():
            self.remove(child)
        
        workspaces_to_show = self.compositor.get_workspaces_for_monitor(gdk_id=gdk_monitor_id)
            
        for ws in workspaces_to_show:
            self.append(WorkspaceButton(ws))
        
        self.on_focused_changed()

    def on_focused_changed(self, *args):
        child = self.get_first_child()
        while child:
            if isinstance(child, WorkspaceButton):
                child._update_state()
            child = child.get_next_sibling()

    def on_scroll(self, controller, dx, dy):
        children = []
        child = self.get_first_child()
        while child:
            if isinstance(child, WorkspaceButton):
                children.append(child)
            child = child.get_next_sibling()
            
        if not children:
            return

        active_index = -1
        for i, btn in enumerate(children):
            if btn.has_css_class("active"):
                active_index = i
                break
        
        target_index = active_index
        if dy > 0: target_index += 1
        elif dy < 0: target_index -= 1
        
        if 0 <= target_index < len(children):
            children[target_index].ws.focus()