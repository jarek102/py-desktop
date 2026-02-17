
import unittest
from unittest.mock import MagicMock

# Define a mock for versions module before importing anything else
import sys
import types
versions_mock = types.ModuleType("versions")
sys.modules["versions"] = versions_mock

# Mock gi repository
gi_mock = types.ModuleType("gi")
gi_repository_mock = types.ModuleType("gi.repository")
gi_mock.repository = gi_repository_mock
sys.modules["gi"] = gi_mock
sys.modules["gi.repository"] = gi_repository_mock

# Mock Gio and GObject
class MockGObject:
    class Object:
        def __init__(self, **kwargs):
            pass
        
        # Minimal GObject.Property mocking for class-level definition
        @staticmethod
        def Property(type=None, default=None, **kwargs):
             # For the class definition, we return a descriptor-like object or just valid value
             # But since we are mocking the class usage in test, we handle it there.
             # This is tricky because the class body runs immediately on import.
             return default

class MockGio:
    class Settings:
        def __init__(self, schema_id):
            self.schema_id = schema_id
            self._data = {}
            self._callbacks = {}
        
        @classmethod
        def new(cls, schema_id):
            return cls(schema_id)
        
        def get_string(self, key):
            return self._data.get(key, "")
        
        def set_string(self, key, value):
            self._data[key] = value
            # In real GSettings, signals are emitted. We can verify calls directly instead.
            
        def connect(self, signal, callback):
            self._callbacks[signal] = callback
            return 1

# Assign mocks
GObject_mock = MockGObject()
Gio_mock = MockGio()

gi_repository_mock.GObject = GObject_mock
gi_repository_mock.Gio = Gio_mock

# Now we can import the service
# BUT: ThemeService inherits from GObject.Object. 
# We need to make sure the import works. 
# The file being tested `src/services/theme_service.py` does `class ThemeService(GObject.Object):`

# Re-importing straightforwardly for testing logic logic inside methods
# We might need to monkeypatch GObject.Property specifically because it changes class attributes.

# Let's use a simpler approach: 
# We will just instantiate the class and verify methods logic, 
# assuming GObject properties work as standard python properties for the logic verification purpose.

# Real import
import os
sys.path.append(os.path.abspath("src"))  # Ensure src is in path

# We need to properly mock GObject.Property logic or the class definition might fail or behave weirdly.
# GObject.Property serves as a descriptor.

class PropertyMock:
    def __init__(self, type=None, default=None, **kwargs):
        self.default = default
        self.name = None
        self.fget = None
        self.fset = None

    def __call__(self, fget):
        # Decorator usage: @GObject.Property(type=...)
        # This instance was created by the call GObject.Property(...) 
        # and now it is being called with the function it decorates.
        self.fget = fget
        return self

    def getter(self, fget):
        self.fget = fget
        return self

    def setter(self, fset):
        self.fset = fset
        return self

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None: return self
        if self.fget:
             return self.fget(instance)
        return instance.__dict__.get(self.name, self.default)

    def __set__(self, instance, value):
        if self.fset:
            self.fset(instance, value)
        else:
            instance.__dict__[self.name] = value

# We need GObject.Property to be a callable that returns a PropertyMock
# OR be the class itself depending on usage.
# Usage 1: is_dark = GObject.Property(...) -> This calls __init__
# Usage 2: @GObject.Property(...) -> This calls __init__, then __call__

GObject_mock.Property = PropertyMock

# Reload module to apply mocks
from services import theme_service
import importlib
importlib.reload(theme_service)

class TestThemeService(unittest.TestCase):
    def setUp(self):
        self.mock_settings = Gio_mock.Settings("org.gnome.desktop.interface")
        self.mock_settings.set_string("color-scheme", "default")
        self.mock_settings.set_string("gtk-theme", "Adwaita")
        
        self.service = theme_service.ThemeService(settings=self.mock_settings)

    def test_initial_sync_light(self):
        # Default is light
        self.mock_settings.set_string("color-scheme", "default")
        self.service._sync_from_settings()
        self.assertFalse(self.service.is_dark)
        
        self.mock_settings.set_string("color-scheme", "prefer-light")
        self.service._sync_from_settings()
        self.assertFalse(self.service.is_dark)

    def test_initial_sync_dark(self):
        self.mock_settings.set_string("color-scheme", "prefer-dark")
        self.service._sync_from_settings()
        self.assertTrue(self.service.is_dark)

    def test_toggle_logic_light_to_dark(self):
        # Start Light
        self.service.is_dark = False 
        self.mock_settings.set_string("gtk-theme", "Adwaita")
        
        # Toggle
        self.service.toggle_mode()
        
        # Verify
        self.assertEqual(self.mock_settings.get_string("color-scheme"), "prefer-dark")
        # GTK theme switching is currently disabled
        self.assertEqual(self.mock_settings.get_string("gtk-theme"), "Adwaita")

    def test_toggle_logic_dark_to_light(self):
        # Start Dark
        self.service.is_dark = True
        self.mock_settings.set_string("gtk-theme", "Adwaita-dark")
        self.mock_settings.set_string("color-scheme", "prefer-dark")

        # Toggle via property setter logic (simulating binding or direct set)
        self.service.is_dark = False
        
        # Verify logic in property setter
        self.assertEqual(self.mock_settings.get_string("color-scheme"), "prefer-light")
        # GTK theme switching is currently disabled
        self.assertEqual(self.mock_settings.get_string("gtk-theme"), "Adwaita-dark")

    def test_toggle_logic_preserves_custom_theme(self):
        # Start Light
        self.service.is_dark = False
        self.mock_settings.set_string("gtk-theme", "Orchis-Red")
        
        # Toggle
        self.service.toggle_mode()
        
        # Expect NO CHANGE (disabled)
        self.assertEqual(self.mock_settings.get_string("gtk-theme"), "Orchis-Red")
        
        # Toggle back
        self.service.toggle_mode()
        self.assertEqual(self.mock_settings.get_string("gtk-theme"), "Orchis-Red")

if __name__ == '__main__':
    unittest.main()
