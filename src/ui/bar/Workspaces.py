import versions
from gi.repository import Gtk, GObject, Gdk
from utils import Blueprint
from services.Compositor import Compositor

@Blueprint("bar/WorkspaceButton.blp")
class WorkspaceButton(Gtk.Button):
    __gtype_name__ = "WorkspaceButton"
    
    id_string = GObject.Property(type=str)

    def __init__(self, ws):
        super().__init__()
        self.ws = ws
        self.id = ws.id
        self.id_string = ""
        self.set_tooltip_text(ws.name)
        
        self.connect("clicked", self.on_clicked)
        
        # Listen for active state changes (specifically for Niri)
        self.ws.connect("notify::is-active", self.update_state)
        self.update_state()

    def on_clicked(self, _):
        self.ws.focus()
        
    def update_state(self, *args):
        is_active = self.ws.is_active or Compositor.get_default().is_workspace_visible(self.id)
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
        
        # Defer initial load until widget is mapped, so we can get the monitor
        self.connect("map", self._on_map)

    def _on_map(self, *args):
        # Run once
        self.disconnect_by_func(self._on_map)
        self.on_workspaces_changed()

    def on_workspaces_changed(self, *args):
        root = self.get_root()
        if not root or not hasattr(root, "get_monitor"):
            return
        
        monitor_id = root.get_monitor()
        display = Gdk.Display.get_default()
        monitor = display.get_monitors().get_item(monitor_id) if display else None
        
        if not monitor:
            return

        # Clear existing children
        while child := self.get_first_child():
            self.remove(child)
        
        monitor_connector = monitor.get_connector()
        
        workspaces_to_show = []
        if self.compositor.is_hyprland:
            workspaces_to_show = [
                ws for ws in self.compositor.workspaces if ws.monitor == monitor_connector
            ]
        elif self.compositor.is_niri:
            # For Niri, show workspaces on this monitor + workspaces on no monitor (unassigned)
            workspaces_to_show = [
                ws for ws in self.compositor.workspaces 
                if ws.monitor == monitor_connector or ws.monitor is None
            ]
        else:
            # Fallback for other/unknown compositors: show all
            workspaces_to_show = self.compositor.workspaces
            
        for ws in workspaces_to_show:
            self.append(WorkspaceButton(ws))
        
        self.on_focused_changed()

    def on_focused_changed(self, *args):
        child = self.get_first_child()
        while child:
            if isinstance(child, WorkspaceButton):
                child.update_state()
            child = child.get_next_sibling()