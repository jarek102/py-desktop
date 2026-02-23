import unittest

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


class MockGObject:
    class Object:
        def __init__(self, **kwargs):
            pass

        @staticmethod
        def Property(type=None, default=None, **kwargs):
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

        def connect(self, signal, callback):
            self._callbacks[signal] = callback
            return 1


GObject_mock = MockGObject()
Gio_mock = MockGio()

gi_repository_mock.GObject = GObject_mock
gi_repository_mock.Gio = Gio_mock

import os

sys.path.append(os.path.abspath("src"))


class PropertyMock:
    def __init__(self, type=None, default=None, **kwargs):
        self.default = default
        self.name = None
        self.fget = None
        self.fset = None

    def __call__(self, fget):
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
        if instance is None:
            return self
        if self.fget:
            return self.fget(instance)
        return instance.__dict__.get(self.name, self.default)

    def __set__(self, instance, value):
        if self.fset:
            self.fset(instance, value)
        else:
            instance.__dict__[self.name] = value


GObject_mock.Property = PropertyMock

from services import theme_service
import importlib

importlib.reload(theme_service)


COUNTERPART_MAP = {
    "Adwaita": {"dark": "Adwaita-dark", "light": None},
    "Adwaita-dark": {"dark": None, "light": "Adwaita"},
    "Orchis-Red-Light": {"dark": "Orchis-Red-Dark", "light": None},
    "Orchis-Red-Dark": {"dark": None, "light": "Orchis-Red-Light"},
}


class TestThemeService(unittest.TestCase):
    def setUp(self):
        self.mock_settings = Gio_mock.Settings("org.gnome.desktop.interface")
        self.mock_settings.set_string("color-scheme", "default")
        self.mock_settings.set_string("gtk-theme", "Adwaita")

        self.service = theme_service.ThemeService(
            settings=self.mock_settings,
            counterpart_map=COUNTERPART_MAP,
        )

    def test_initial_sync_light(self):
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

    def test_toggle_logic_light_to_dark_updates_theme_by_counterpart(self):
        self.service.is_dark = False
        self.mock_settings.set_string("gtk-theme", "Adwaita")

        self.service.toggle_mode()

        self.assertEqual(self.mock_settings.get_string("color-scheme"), "prefer-dark")
        self.assertEqual(self.mock_settings.get_string("gtk-theme"), "Adwaita-dark")

    def test_toggle_logic_dark_to_light_updates_theme_by_counterpart(self):
        self.service.is_dark = True
        self.mock_settings.set_string("gtk-theme", "Adwaita-dark")
        self.mock_settings.set_string("color-scheme", "prefer-dark")

        self.service.is_dark = False

        self.assertEqual(self.mock_settings.get_string("color-scheme"), "prefer-light")
        self.assertEqual(self.mock_settings.get_string("gtk-theme"), "Adwaita")

    def test_toggle_logic_preserves_custom_theme_when_no_counterpart(self):
        self.service.is_dark = False
        self.mock_settings.set_string("gtk-theme", "UnknownTheme")

        self.service.toggle_mode()

        self.assertEqual(self.mock_settings.get_string("color-scheme"), "prefer-dark")
        self.assertEqual(self.mock_settings.get_string("gtk-theme"), "UnknownTheme")

    def test_custom_theme_counterpart_switches_both_directions(self):
        self.service.is_dark = False
        self.mock_settings.set_string("gtk-theme", "Orchis-Red-Light")

        self.service.toggle_mode()
        self.assertEqual(self.mock_settings.get_string("gtk-theme"), "Orchis-Red-Dark")

        self.service.toggle_mode()
        self.assertEqual(self.mock_settings.get_string("gtk-theme"), "Orchis-Red-Light")


if __name__ == "__main__":
    unittest.main()
