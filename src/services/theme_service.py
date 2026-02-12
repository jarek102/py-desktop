from __future__ import annotations

import enum

import versions
from gi.repository import Gio, GObject


class ThemeMode(str, enum.Enum):
    LIGHT = "light"
    DARK = "dark"


class ThemeService(GObject.Object):
    mode = GObject.Property(type=str, default=ThemeMode.LIGHT.value)
    is_dark = GObject.Property(type=bool, default=False)

    def __init__(self, settings: Gio.Settings | None = None):
        super().__init__()
        self._settings = settings or Gio.Settings.new("org.gnome.desktop.interface")

        # Bind is_dark to be true when mode is "dark"
        self.bind_property(
            "mode",
            self,
            "is_dark",
            GObject.BindingFlags.SYNC_CREATE,
            lambda _, mode_str: mode_str == ThemeMode.DARK.value,
        )

        self._settings.connect("changed::color-scheme", self._sync_from_settings)
        self._sync_from_settings()

    def _sync_from_settings(self, *_args) -> None:
        color_scheme = self._settings.get_string("color-scheme")
        self.mode = (
            ThemeMode.DARK.value
            if color_scheme == "prefer-dark"
            else ThemeMode.LIGHT.value
        )

    def get_mode(self) -> ThemeMode:
        if self.mode == ThemeMode.DARK.value:
            return ThemeMode.DARK
        return ThemeMode.LIGHT

    def set_mode(self, mode: ThemeMode | str) -> None:
        value = mode.value if isinstance(mode, ThemeMode) else str(mode)
        if value not in (ThemeMode.LIGHT.value, ThemeMode.DARK.value):
            return
        self._settings.set_string(
            "color-scheme",
            "prefer-dark" if value == ThemeMode.DARK.value else "default",
        )
        self.mode = value

    def toggle_mode(self) -> ThemeMode:
        next_mode = (
            ThemeMode.LIGHT
            if self.get_mode() == ThemeMode.DARK
            else ThemeMode.DARK
        )
        self.set_mode(next_mode)
        return next_mode
