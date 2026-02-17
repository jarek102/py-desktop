import logging
import os
from typing import Optional
import versions
from gi.repository import GObject, Gdk, GLib, AstalHyprland, AstalNiri
from services.compositor_match import MonitorTarget, workspace_matches_monitor
from services.scroll_ipc import ScrollIPC, ScrollWorkspace as ScrollIPCWorkspace

_log = logging.getLogger("py_desktop.compositor")
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

class Monitor(GObject.Object):
    __gtype_name__ = "CompositorMonitor"
    
    gdk_id = GObject.Property(type=int)
    gdk_monitor = GObject.Property(type=Gdk.Monitor)
    name = GObject.Property(type=str)
    # hyprland only
    object = GObject.Property(type=AstalHyprland.Monitor)
    id = GObject.Property(type=int)

    def __init__(self, native, compositor_type=None, niri_connector=None):
        super().__init__()
        self.native = native
        self.compositor_type = compositor_type
        self._hyprland_bound = False
        self._niri_bound = False
        
        match compositor_type:
            case "hyprland":
                self.bind_hyprland(native)
            case "niri":
                self.bind_niri(native, niri_connector)

    def bind_hyprland(self, native):
        if native is None:
            return
        self.native = native
        self.compositor_type = "hyprland"
        if not self._hyprland_bound:
            native.bind_property("id", self, "id", GObject.BindingFlags.SYNC_CREATE)
            native.bind_property("name", self, "name", GObject.BindingFlags.SYNC_CREATE)
            self._hyprland_bound = True
        self.set_property("object", native)

    def bind_niri(self, native=None, niri_connector=None):
        self.native = native
        self.compositor_type = "niri"
        if native is not None and not self._niri_bound:
            native.bind_property("name", self, "name", GObject.BindingFlags.SYNC_CREATE)
            self._niri_bound = True
        elif niri_connector:
            self.set_property("name", niri_connector)

    def update_gdk(self, gdk_monitor=None, gdk_id=None):
        if gdk_monitor is not None:
            self.gdk_monitor = gdk_monitor
            if not self.name:
                connector = gdk_monitor.get_connector()
                if connector:
                    self.name = connector
        if gdk_id is not None:
            self.gdk_id = gdk_id

    @staticmethod
    def from_niri_connector(niri_connector):
        return Compositor.get_default().get_monitor_for_niri_connector(niri_connector)
            
    def get_api_monitor(self):
        match self.compositor_type:
            case "hyprland":
                return self.object
            case "niri":
                return self.name
        
class Workspace(GObject.Object):
    __gtype_name__ = "CompositorWorkspace"
    
    id = GObject.Property(type=int, default=0)
    name = GObject.Property(type=str, default="")
    monitor = GObject.Property(type=Monitor, default=None)
    is_active = GObject.Property(type=bool, default=False)
    is_focused = GObject.Property(type=bool, default=False)

    def __init__(self, native_workspace, compositor_type=None):
        super().__init__()
        self.native = native_workspace
        self.compositor_type = compositor_type
        self._hypr_focused_binding = None
        self._hypr_active_binding = None
        
        match compositor_type:
            case "hyprland":
                native_workspace.bind_property("id", self, "id", GObject.BindingFlags.SYNC_CREATE)
                native_workspace.bind_property("name", self, "name", GObject.BindingFlags.SYNC_CREATE)
                self._on_hyprland_monitor_changed()
                native_workspace.connect("notify::monitor", self._on_hyprland_monitor_changed)
            case "niri":
                native_workspace.bind_property("id", self, "id", GObject.BindingFlags.SYNC_CREATE)
                native_workspace.bind_property("name", self, "name", GObject.BindingFlags.SYNC_CREATE)
                native_workspace.bind_property("is_active", self, "is_active", GObject.BindingFlags.SYNC_CREATE)
                native_workspace.bind_property("is_focused", self, "is_focused", GObject.BindingFlags.SYNC_CREATE)
                self._on_niri_output_changed(native_workspace)
                native_workspace.connect("notify::output", self._on_niri_output_changed)
            case "scroll":
                self.id = int(getattr(native_workspace, "num", 0))
                self.name = str(getattr(native_workspace, "name", self.id))
                self.is_active = bool(getattr(native_workspace, "visible", False))
                self.is_focused = bool(getattr(native_workspace, "focused", False))
                output = getattr(native_workspace, "output", None)
                if output:
                    self.monitor = Compositor.get_default().get_monitor_for_niri_connector(output)
    
    def _on_hyprland_monitor_changed(self, *args):
        hypr_monitor = getattr(self.native.props, "monitor", None)
        if hypr_monitor is None:
            _log.warning(
                "Workspace id=%s name=%s has no monitor; skipping monitor bindings",
                self.id,
                self.name,
            )
            self.monitor = None
            self.is_focused = False
            self.is_active = False
            return

        if self._hypr_focused_binding is not None:
            self._hypr_focused_binding.unbind()
            self._hypr_focused_binding = None
        if self._hypr_active_binding is not None:
            self._hypr_active_binding.unbind()
            self._hypr_active_binding = None

        self.monitor = Compositor.get_default().get_monitor_for_hyprland(hypr_monitor)
        self._hypr_focused_binding = hypr_monitor.bind_property(
            "focused",
            self,
            "is_focused",
            GObject.BindingFlags.SYNC_CREATE,
        )
        self._hypr_active_binding = hypr_monitor.bind_property(
            "active_workspace",
            self,
            "is_active",
            GObject.BindingFlags.SYNC_CREATE,
            lambda _binding, workspace: bool(
                workspace is not None and workspace.props.id == self.id
            ),
        )

    def _on_niri_output_changed(self, *args):
        output = getattr(self.native.props, "output", None)
        if output:
            # Niri workspace output is a connector string
            self.monitor = Compositor.get_default().get_monitor_for_niri_connector(output)

    def focus(self):
        self.native.focus()


class ScrollWorkspaceHandle:
    def __init__(self, workspace: ScrollIPCWorkspace, ipc: ScrollIPC):
        self.num = workspace.num
        self.name = workspace.name
        self.output = workspace.output
        self.focused = workspace.focused
        self.visible = workspace.visible
        self._ipc = ipc

    def focus(self):
        ws = ScrollIPCWorkspace(
            num=self.num,
            name=self.name,
            output=self.output,
            focused=self.focused,
            visible=self.visible,
        )
        self._ipc.focus_workspace(ws)

class MonitorManager:
    def __init__(self, gdk_display, niri=None, hyprland=None):
        self._gdk_display = gdk_display
        self._niri = niri
        self._hyprland = hyprland

        self._monitors = []
        self._monitors_by_name = {}
        self._monitors_by_gdk_monitor = {}
        self._monitors_by_gdk_id = {}

        self._sync_gdk_monitors()
        if self._gdk_display is not None:
            monitors = self._gdk_display.get_monitors()
            monitors.connect("items-changed", self._sync_gdk_monitors)

        if self._niri is not None:
            self._niri.connect("notify::outputs", self._sync_niri_outputs)
            self._sync_niri_outputs()

        if self._hyprland is not None:
            self._hyprland.connect("notify::monitors", self._sync_hyprland_monitors)
            self._sync_hyprland_monitors()

    @property
    def monitors(self):
        return self._monitors

    def _get_or_create_monitor_by_name(self, name):
        if name and name in self._monitors_by_name:
            return self._monitors_by_name[name]
        monitor = Monitor(None)
        if name:
            monitor.name = name
            self._monitors_by_name[name] = monitor
        self._monitors.append(monitor)
        return monitor

    def get_monitor_for_gdk_monitor(self, gdk_monitor, gdk_id=None):
        if gdk_monitor is None:
            return None
        monitor = self._monitors_by_gdk_monitor.get(gdk_monitor)
        if monitor is None:
            name = gdk_monitor.get_connector()
            monitor = self._get_or_create_monitor_by_name(name)
        monitor.update_gdk(gdk_monitor, gdk_id)
        self._monitors_by_gdk_monitor[gdk_monitor] = monitor
        if gdk_id is not None:
            self._monitors_by_gdk_id[gdk_id] = monitor
        return monitor

    def get_monitor_for_hyprland(self, hypr_monitor):
        if hypr_monitor is None:
            return None
        name = getattr(hypr_monitor.props, "name", None)
        monitor = self._get_or_create_monitor_by_name(name)
        monitor.bind_hyprland(hypr_monitor)
        return monitor

    def get_monitor_for_niri_output(self, output):
        if output is None:
            return None
        name = getattr(output.props, "name", None)
        monitor = self._get_or_create_monitor_by_name(name)
        monitor.bind_niri(output, name)
        return monitor

    def get_monitor_for_niri_connector(self, connector):
        if not connector:
            return None
        if self._niri is not None:
            for output in self._niri.get_outputs():
                name = getattr(output.props, "name", None)
                if name == connector:
                    return self.get_monitor_for_niri_output(output)
        monitor = self._get_or_create_monitor_by_name(connector)
        monitor.bind_niri(None, connector)
        return monitor

    def _sync_gdk_monitors(self, *args):
        if self._gdk_display is None:
            return
        monitors = self._gdk_display.get_monitors()
        by_gdk = {}
        by_gdk_id = {}
        for i in range(monitors.get_n_items()):
            gdk_monitor = monitors.get_item(i)
            if not gdk_monitor:
                continue
            monitor = self.get_monitor_for_gdk_monitor(gdk_monitor, i)
            by_gdk[gdk_monitor] = monitor
            by_gdk_id[i] = monitor
        self._monitors_by_gdk_monitor = by_gdk
        self._monitors_by_gdk_id = by_gdk_id

    def _sync_niri_outputs(self, *args):
        if self._niri is None:
            return
        for output in self._niri.get_outputs():
            self.get_monitor_for_niri_output(output)

    def _sync_hyprland_monitors(self, *args):
        if self._hyprland is None:
            return
        for h_mon in self._hyprland.get_monitors():
            self.get_monitor_for_hyprland(h_mon)

class Compositor(GObject.GObject):
    _instance = None
    
    __gsignals__ = {
        'workspaces-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    @classmethod
    def get_default(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        super().__init__()
        # Allow re-entrant calls to Compositor.get_default() during construction.
        Compositor._instance = self
        self._desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        self._hyprland: Optional[AstalHyprland.Hyprland] = None
        self._niri: Optional[AstalNiri.Niri] = None
        self._scroll: Optional[ScrollIPC] = None
        self._gdk_display = Gdk.Display.get_default()
        self._monitor_manager = None
        
        self._workspaces = []
        
        if "hyprland" in self._desktop:
            self._hyprland = AstalHyprland.get_default()
            self._hyprland.connect("notify::workspaces", self._sync_hyprland_workspaces)
        elif "niri" in self._desktop:
            self._niri = AstalNiri.get_default()
            self._niri.connect("notify::workspaces", self._sync_niri_workspaces)
        elif "scroll" in self._desktop:
            self._scroll = ScrollIPC()
        
        self._monitor_manager = MonitorManager(
            self._gdk_display,
            niri=self._niri,
            hyprland=self._hyprland,
        )

        if self.is_hyprland:
            self._sync_hyprland_workspaces()
        elif self.is_niri:
            self._sync_niri_workspaces()
        elif self.is_scroll:
            self._sync_scroll_workspaces()
            if self._scroll is not None:
                self._scroll.start_event_monitor(self._on_scroll_event)

    @property
    def is_hyprland(self):
        return "hyprland" in self._desktop

    @property
    def is_niri(self):
        return "niri" in self._desktop

    @property
    def is_scroll(self):
        return "scroll" in self._desktop

    @property
    def hyprland(self):
        return self._hyprland
        
    @property
    def workspaces(self):
        return self._workspaces
        

    @property
    def monitors(self):
        return self._monitor_manager.monitors

    def get_monitor_for_gdk_monitor(self, gdk_monitor, gdk_id=None):
        return self._monitor_manager.get_monitor_for_gdk_monitor(gdk_monitor, gdk_id)

    def get_monitor_for_hyprland(self, hypr_monitor):
        return self._monitor_manager.get_monitor_for_hyprland(hypr_monitor)

    def get_monitor_for_niri_output(self, output):
        return self._monitor_manager.get_monitor_for_niri_output(output)

    def get_monitor_for_niri_connector(self, connector):
        return self._monitor_manager.get_monitor_for_niri_connector(connector)

    def get_workspaces_for_monitor(self, monitor=None, gdk_id=None, gdk_monitor=None):
        target_monitor = None
        if isinstance(monitor, Monitor):
            target_monitor = monitor
        elif isinstance(monitor, Gdk.Monitor):
            gdk_monitor = monitor

        target = MonitorTarget(
            monitor=target_monitor,
            gdk_id=gdk_id,
            gdk_monitor=gdk_monitor,
        )
        return [
            ws
            for ws in self._workspaces
            if workspace_matches_monitor(ws.monitor, target)
        ]

    def do_screen_transition(self, delay_ms=0):
        """
        Triggers a screen transition if the compositor supports it.
        Currently only implemented for Niri.
        """
        if self.is_niri:
            try:
                # Use GLib.Variant for int64 as per our fix in AstalNiri
                v_delay = GLib.Variant('x', delay_ms)
                AstalNiri.msg.do_screen_transition(v_delay)
            except Exception as e:
                _log.warning(f"Failed to trigger Niri screen transition: {e}")

    def logout(self):
        if self.is_hyprland and self._hyprland is not None:
             self._hyprland.dispatch("exit", "")
        elif self.is_niri:
             AstalNiri.msg.quit(True)
        elif self.is_scroll:
             if self._scroll is not None:
                 self._scroll.stop_event_monitor()
                 self._scroll.quit()

    def _sync_hyprland_workspaces(self, *args):
        _log.info("Sync hyprland workspaces")
        ws_list = []
        for h_ws in sorted(self._hyprland.props.workspaces, key=lambda w: w.props.id):
            if h_ws.props.id >= 0:
                ws_list.append(Workspace(h_ws, "hyprland"))
        
        self._workspaces = ws_list
        _log.info("Hyprland workspaces count=%s ids=%s", len(self._workspaces), [w.id for w in self._workspaces])
        self.emit("workspaces-changed")

    def _sync_niri_workspaces(self, *args):
        _log.info("Sync niri workspaces")
        ws_list = []
        for n_ws in self._niri.get_workspaces():
            ws_list.append(Workspace(n_ws, "niri"))
            
        self._workspaces = sorted(ws_list, key=lambda w: w.id if isinstance(w.id, int) else str(w.id))
        _log.info("Niri workspaces count=%s ids=%s", len(self._workspaces), [w.id for w in self._workspaces])
        self.emit("workspaces-changed")

    def _on_scroll_event(self):
        GLib.idle_add(self._sync_scroll_workspaces)

    def _sync_scroll_workspaces(self, *args):
        if self._scroll is None:
            return
        _log.debug("Sync scroll workspaces")
        ws_list = []
        for scroll_ws in self._scroll.get_workspaces():
            handle = ScrollWorkspaceHandle(scroll_ws, self._scroll)
            workspace = Workspace(handle, "scroll")
            ws_list.append(workspace)

        self._workspaces = sorted(ws_list, key=lambda w: w.id if isinstance(w.id, int) else str(w.id))
        self.emit("workspaces-changed")
