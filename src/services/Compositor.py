import os
import versions
from gi.repository import GObject, AstalHyprland, AstalNiri

class Workspace(GObject.Object):
    __gtype_name__ = "CompositorWorkspace"
    
    def __init__(self, id, name, focus_func):
        super().__init__()
        self.id = id
        self.name = name
        self._focus_func = focus_func
        
    def focus(self):
        if self._focus_func:
            self._focus_func()

class Compositor(GObject.GObject):
    _instance = None
    
    __gsignals__ = {
        'workspaces-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'focused-workspace-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    @classmethod
    def get_default(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        super().__init__()
        self._desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        self._hyprland = None
        self._niri = None
        
        self._workspaces = []
        self._focused_workspace = None
        
        if "hyprland" in self._desktop:
            self._hyprland = AstalHyprland.get_default()
            self._hyprland.connect("notify::workspaces", self._sync_hyprland_workspaces)
            self._hyprland.connect("notify::focused-workspace", self._sync_hyprland_focus)
            self._sync_hyprland_workspaces()
            
        elif "niri" in self._desktop:
            self._niri = AstalNiri.get_default()
            self._niri.connect("notify::workspaces", self._sync_niri_workspaces)
            self._niri.connect("notify::focused-workspace", self._sync_niri_focus)
            self._sync_niri_workspaces()

    @property
    def is_hyprland(self):
        return "hyprland" in self._desktop

    @property
    def is_niri(self):
        return "niri" in self._desktop

    @property
    def hyprland(self):
        return self._hyprland
        
    @property
    def workspaces(self):
        return self._workspaces
        
    @property
    def focused_workspace(self):
        return self._focused_workspace

    def _sync_hyprland_workspaces(self, *args):
        ws_list = []
        for h_ws in sorted(self._hyprland.workspaces, key=lambda w: w.id):
            if h_ws.id >= 0:
                ws_list.append(Workspace(h_ws.id, str(h_ws.name), h_ws.focus))
        
        self._workspaces = ws_list
        self.emit("workspaces-changed")
        self._sync_hyprland_focus()

    def _sync_hyprland_focus(self, *args):
        h_focused = self._hyprland.focused_workspace
        if h_focused:
            self._focused_workspace = next((w for w in self._workspaces if w.id == h_focused.id), None)
        else:
            self._focused_workspace = None
        self.emit("focused-workspace-changed")

    def _sync_niri_workspaces(self, *args):
        ws_list = []
        for n_ws in self._niri.workspaces:
            # Handle Niri workspace properties safely
            wid = getattr(n_ws, "id", getattr(n_ws, "idx", 0))
            wname = getattr(n_ws, "name", str(wid))
            if not wname: wname = str(wid)
            
            ws_list.append(Workspace(wid, wname, n_ws.focus))
            
        self._workspaces = sorted(ws_list, key=lambda w: w.id if isinstance(w.id, int) else str(w.id))
        self.emit("workspaces-changed")
        self._sync_niri_focus()

    def _sync_niri_focus(self, *args):
        n_focused = self._niri.focused_workspace
        if n_focused:
            fid = getattr(n_focused, "id", getattr(n_focused, "idx", 0))
            self._focused_workspace = next((w for w in self._workspaces if w.id == fid), None)
        else:
            self._focused_workspace = None
        self.emit("focused-workspace-changed")