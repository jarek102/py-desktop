import pathlib
import json

from gi.repository import Astal, AstalNiri, Gio, AstalIO
from ui.quicksettings.DeviceMenuWindow import DeviceMenuWindow
from ui.bar.Bar import Bar
from ui.common.Overlay import Overlay

BASE_DIR = pathlib.Path(__file__).resolve().parent
CSS_FILE = BASE_DIR.parent / 'generated' / 'style.css'

class App(Astal.Application):
    system_menu = None
    bars = {}
    overlays = {}
    active_popup = None
    
    def __init__(self,instance_name = "py_desktop", **kwargs):
        super().__init__(
            instance_name = instance_name,
            application_id='com.github.jarek102.py-desktop',
            **kwargs)
            
        from services.theme_service import ThemeService
        self.theme_service = ThemeService.get_default()
        self.current_theme_class = f"theme-{self.theme_service.theme_family}"
        
        self.connect('activate', self.on_activate)
        self.connect('window-added', self._on_window_added)
        self.theme_service.connect('notify::theme-family', self._on_theme_family_changed)
        
    def _on_theme_family_changed(self, *_args):
        new_class = f"theme-{self.theme_service.theme_family}"
        if self.current_theme_class != new_class:
            for win in self.get_windows():
                win.remove_css_class(self.current_theme_class)
                win.add_css_class(new_class)
            self.current_theme_class = new_class

    def _on_window_added(self, _app, window):
        window.add_css_class(self.current_theme_class)
    
    def on_activate(self,_):
        self.apply_css(CSS_FILE.as_posix(), True)
        if not self.bars:
            for mon in self.get_monitors():
                self.bars[mon] = Bar(gdkmonitor=mon,window_manager=self)
                self.add_window(self.bars[mon])
        for bar in self.bars.values():
            bar.present()
        
    def _ensure_overlays(self):
        if not self.overlays:
            for mon in self.get_monitors():
                self.overlays[mon] = Overlay(self.close_popups, gdkmonitor=mon)
                self.add_window(self.overlays[mon])

    def show_popup(self, window):
        self._ensure_overlays()
        
        if self.active_popup and self.active_popup != window:
            self.active_popup.hide()
            
        self.active_popup = window
        
        for ov in self.overlays.values():
            ov.show()
            
        window.show()

    def close_popups(self):
        if self.active_popup:
            self.active_popup.hide()
            self.active_popup = None
        
        for ov in self.overlays.values():
            ov.hide()

    def toggle_device_menu(self, gdkmonitor=None):
        if not self.system_menu:
            self.system_menu = DeviceMenuWindow()
            self.add_window(self.system_menu)
        if gdkmonitor is not None and self.system_menu.get_monitor() != gdkmonitor:
            self.system_menu.set_monitor(gdkmonitor)
        
        if self.system_menu.is_visible():
            self.close_popups()
        else:
            self.show_popup(self.system_menu)

    def do_astal_application_request(self, msg: str, conn: Gio.SocketConnection) -> None:
        request = (msg or "").strip().lower()

        if request == "ping":
            AstalIO.write_sock(conn, "pong")
            return

        if request == "status":
            payload = {
                "instance_name": self.props.instance_name,
                "bars": len(self.bars),
                "overlays": len(self.overlays),
                "popup_open": self.active_popup is not None,
                "device_menu_visible": bool(
                    self.system_menu is not None and self.system_menu.is_visible()
                ),
            }
            AstalIO.write_sock(conn, json.dumps(payload))
            return

        if request == "toggle-device-menu":
            self.toggle_device_menu()
            payload = {
                "popup_open": self.active_popup is not None,
                "device_menu_visible": bool(
                    self.system_menu is not None and self.system_menu.is_visible()
                ),
            }
            AstalIO.write_sock(conn, json.dumps(payload))
            return

        if request == "close-popups":
            self.close_popups()
            AstalIO.write_sock(conn, "ok")
            return

        AstalIO.write_sock(conn, f"unknown request: {request}")
