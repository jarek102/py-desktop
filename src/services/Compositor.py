import os
import versions
from gi.repository import GObject, AstalHyprland, AstalNiri

class Workspace(GObject.Object):
    __gtype_name__ = "CompositorWorkspace"
    
    id = GObject.Property(type=int, default=0)
    name = GObject.Property(type=str, default="")
    monitor = GObject.Property(type=str)
    is_active = GObject.Property(type=bool, default=False)

    def __init__(self, native, compositor_type=None):
        super().__init__()
        self.native = native
        self.compositor_type = compositor_type
        self.sync()
        self.native.connect("notify", self._on_notify)

    def _on_notify(self, source, pspec):
        self.sync()
        
    def sync(self):
        if self.compositor_type == "niri":
            # Niri
            if hasattr(self.native, "id"):
                self.id = self.native.id
            elif hasattr(self.native, "get_id"):
                self.id = self.native.get_id()
            else:
                self.id = getattr(self.native, "idx", 0)

            wname = getattr(self.native, "name", None)
            if wname is None and hasattr(self.native, "get_name"):
                wname = self.native.get_name()
            self.name = str(wname) if wname else str(self.id)
            
            self.monitor = getattr(self.native, "output", getattr(self.native, "get_output", lambda: None)())
            
            val = getattr(self.native, "is_active", False)
            if callable(val):
                val = val()
            self.is_active = bool(val)
        elif self.compositor_type == "hyprland":
            # Hyprland
            self.id = self.native.id
            self.name = self.native.name
            # Handle AstalHyprland Monitor object
            mon = self.native.monitor
            self.monitor = mon.name if hasattr(mon, "name") else mon
        else:
            # Fallback
            self.id = getattr(self.native, "id", 0)
            self.name = str(getattr(self.native, "name", ""))
        
    def focus(self):
        self.native.focus()

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
                ws_list.append(Workspace(h_ws, "hyprland"))
        
        self._workspaces = ws_list
        self.emit("workspaces-changed")
        self._sync_hyprland_focus()

    def _sync_hyprland_focus(self, *args):
        h_focused = self._hyprland.focused_workspace
        if h_focused:
            found = next((w for w in self._workspaces if w.id == h_focused.id), None)
            if not found:
                # Fallback if workspace is not in the list (e.g. filtered out or race condition)
                found = Workspace(h_focused, "hyprland")
            self._focused_workspace = found
        else:
            self._focused_workspace = None
        self.emit("focused-workspace-changed")

    def is_workspace_visible(self, id) -> bool:
        if self.is_hyprland:
            for m in self._hyprland.monitors:
                if m.active_workspace and m.active_workspace.id == id:
                    return True
        
        if self.is_niri:
            for ws in self._workspaces:
                if ws.id == id and ws.is_active:
                    return True
            
            # Fallback: Check monitors for active workspace (if property didn't update)
            monitors = getattr(self._niri, "monitors", None)
            if monitors:
                for m in monitors:
                    aw = getattr(m, "active_workspace", None)
                    if aw and aw.id == id:
                        return True
                    aw_id = getattr(m, "active_workspace_id", None)
                    if aw_id == id:
                        return True
        
        if self._focused_workspace and self._focused_workspace.id == id:
            return True
            
        return False

    def _sync_niri_workspaces(self, *args):
        ws_list = []
        for n_ws in self._niri.get_workspaces():
            ws_list.append(Workspace(n_ws, "niri"))
            
        self._workspaces = sorted(ws_list, key=lambda w: w.id if isinstance(w.id, int) else str(w.id))
        self.emit("workspaces-changed")
        self._sync_niri_focus()

    def _sync_niri_focus(self, *args):
        n_focused = self._niri.get_focused_workspace()
        if n_focused:
            fid = getattr(n_focused, "id", getattr(n_focused, "idx", 0))
            found = next((w for w in self._workspaces if w.id == fid), None)
            if not found:
                found = Workspace(n_focused, "niri")
            self._focused_workspace = found
        else:
            self._focused_workspace = None
        self.emit("focused-workspace-changed")