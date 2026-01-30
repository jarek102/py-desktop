import versions
from gi.repository import Gtk, GObject
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
        self.id_string = ws.name
        
        self.connect("clicked", self.on_clicked)

    def on_clicked(self, _):
        self.ws.focus()

@Blueprint("bar/Workspaces.blp")
class Workspaces(Gtk.Box):
    __gtype_name__ = "Workspaces"

    def __init__(self):
        super().__init__()
        self.compositor = Compositor.get_default()
        self.compositor.connect("workspaces-changed", self.on_workspaces_changed)
        self.compositor.connect("focused-workspace-changed", self.on_focused_changed)
        
        # Initial load
        self.on_workspaces_changed()

    def on_workspaces_changed(self, *args):
        # Clear existing children
        while child := self.get_first_child():
            self.remove(child)
            
        for ws in self.compositor.workspaces:
            self.append(WorkspaceButton(ws))
        
        self.on_focused_changed()

    def on_focused_changed(self, *args):
        focused = self.compositor.focused_workspace

        child = self.get_first_child()
        while child:
            if isinstance(child, WorkspaceButton):
                if focused and child.id == focused.id:
                    child.add_css_class("active")
                else:
                    child.remove_css_class("active")
            child = child.get_next_sibling()