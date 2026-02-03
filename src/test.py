#!/usr/bin/env python3

import sys
import pathlib
from ctypes import CDLL

try:
    CDLL('libgtk4-layer-shell.so')
except OSError:
    print("Error: 'libgtk4-layer-shell.so' not found. Please ensure gtk4-layer-shell is installed.")
    sys.exit(1)

import versions
from gi.repository import Astal, AstalNiri, Gtk, Gdk, Gio, GObject

BASE_DIR = pathlib.Path(__file__).resolve().parent
CSS_FILE = BASE_DIR.parent / 'generated' / 'style.css'

class Win(Astal.Window):

    store = Gio.ListStore(item_type=AstalNiri.Workspace)

    def __init__(self, **kwargs):
        super().__init__(
            anchor = Astal.WindowAnchor.BOTTOM,
            **kwargs)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.props.margin_top = 24
        box.props.margin_bottom = 24
        box.props.margin_start = 24
        box.props.margin_end = 24
        
        label = Gtk.Label(label="Niri Notify")
        box.append(label)
    
        niri = AstalNiri.get_default()
        niri.connect("notify", self.on_workspaces_changed)
        self.on_workspaces_changed()

        cv = Gtk.ColumnView()
        cv.set_model(Gtk.SingleSelection(model=self.store))
        cv.set_vexpand(True)

        for title, attr in [("ID", "id"), ("Name", "name")]:
            factory = Gtk.SignalListItemFactory()
            factory.connect("setup", lambda _, item: item.set_child(Gtk.Label(halign=Gtk.Align.START)))
            factory.connect("bind", lambda _, item, a=attr: item.get_child().set_label(str(getattr(item.get_item(), a, "N/A"))))
            cv.append_column(Gtk.ColumnViewColumn(title=title, factory=factory))

        sw = Gtk.ScrolledWindow(min_content_height=200)
        sw.set_child(cv)
        box.append(sw)
        
        self.set_child(box)

    def on_workspaces_changed(self, *args):
        niri = AstalNiri.get_default()
        self.store.remove_all()
        for ws in niri.props.workspaces:
            self.store.append(ws)

class App(Astal.Application):
    def __init__(self):
        super().__init__(
            instance_name="test_app",
            application_id="com.github.jarek102.py-desktop-test"
        )
        self.connect("activate", self.on_activate)

    def on_activate(self, *args):
        if CSS_FILE.exists():
            print(f"Loading CSS from {CSS_FILE}")
            self.apply_css(CSS_FILE.as_posix(), True)
            
        win = Win(application=self)
        win.present()

if __name__ == "__main__":
    app = App()
    sys.exit(app.run(None))