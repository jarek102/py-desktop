from __future__ import annotations

import json
import logging
import os

_log = logging.getLogger(__name__)

import versions
from gi.repository import Gio, GObject


DEFAULT_THEMES_INDEX_PATH = os.path.expanduser("~/.config/theme-switcher/themes.json")


class ThemeService(GObject.Object):
    _instance = None
    _is_dark = False
    _theme_family = "default"

    @classmethod
    def get_default(cls) -> "ThemeService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(
        self,
        settings: Gio.Settings | None = None,
        themes_index_path: str | None = None,
        counterpart_map: dict[str, dict[str, str | None]] | None = None,
        theme_family_map: dict[str, str] | None = None,
    ):
        super().__init__()
        if ThemeService._instance is not None:
             raise RuntimeError("ThemeService is a singleton. Use ThemeService.get_default()")
        ThemeService._instance = self

        self._settings = settings or Gio.Settings.new("org.gnome.desktop.interface")
        self._themes_index_path = themes_index_path or DEFAULT_THEMES_INDEX_PATH
        
        # Load maps
        maps = self._load_theme_maps() if (counterpart_map is None or theme_family_map is None) else (counterpart_map, theme_family_map)
        self._counterpart_map = counterpart_map if counterpart_map is not None else maps[0]
        self._theme_family_map = theme_family_map if theme_family_map is not None else maps[1]

        self._settings.connect("changed::color-scheme", self._sync_from_settings)
        self._settings.connect("changed::gtk-theme", self._sync_theme_family)
        self._sync_from_settings()
        self._sync_theme_family()

    @GObject.Property(type=str, default="default")
    def theme_family(self) -> str:  # type: ignore[reportRedeclaration]
        return self._theme_family

    @theme_family.setter
    def theme_family(self, value: str):
        self._theme_family = value

    @GObject.Property(type=bool, default=False)
    def is_dark(self) -> bool:  # type: ignore[reportRedeclaration]
        return self._is_dark

    @is_dark.setter
    def is_dark(self, value: bool):
        self._is_dark = value

        color_scheme = self._settings.get_string("color-scheme")
        if value == (color_scheme == "prefer-dark"):
            return

        try:
            from services.Compositor import Compositor
            Compositor.get_default().do_screen_transition(500)
        except Exception as error:
            _log.warning(f"Failed to trigger screen transition: {error}")

        new_scheme = "prefer-dark" if value else "prefer-light"
        self._settings.set_string("color-scheme", new_scheme)

        current_theme = self._settings.get_string("gtk-theme")
        next_theme = self._resolve_theme_for_mode(current_theme, target_dark=value)
        if next_theme and next_theme != current_theme:
            self._settings.set_string("gtk-theme", next_theme)


    def _load_theme_maps(self) -> tuple[dict[str, dict[str, str | None]], dict[str, str]]:
        if not os.path.exists(self._themes_index_path):
            _log.info("Theme index not found at %s; counterpart switching disabled", self._themes_index_path)
            return {}, {}

        try:
            with open(self._themes_index_path, "r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
        except (OSError, json.JSONDecodeError) as error:
            _log.warning("Failed to load theme index from %s: %s", self._themes_index_path, error)
            return {}, {}

        counterpart_map: dict[str, dict[str, str | None]] = {}
        theme_family_map: dict[str, str] = {}
        
        if not isinstance(data, dict):
            return counterpart_map, theme_family_map

        for family_data in data.values():
            if not isinstance(family_data, dict):
                continue
            variants = family_data.get("variants")
            if not isinstance(variants, dict):
                continue

            for variant_name, variant_data in variants.items():
                if not isinstance(variant_data, dict):
                    continue
                # Map variant back to its normalised family alias (e.g. Arc, Colloid)
                theme_family_map[variant_name] = family_data.get("description", {}).get("family_label", variant_name.split("-")[0]).lower()
                
                raw_counterparts = variant_data.get("counterparts", {})
                if not isinstance(raw_counterparts, dict):
                    raw_counterparts = {}

                counterpart_map[variant_name] = {
                    "dark": raw_counterparts.get("dark"),
                    "light": raw_counterparts.get("light"),
                }

        return counterpart_map, theme_family_map


    def _resolve_theme_for_mode(self, current_theme: str, target_dark: bool) -> str | None:
        if not current_theme:
            return None

        counterpart_entry = self._counterpart_map.get(current_theme)
        if not counterpart_entry:
            return None

        target_key = "dark" if target_dark else "light"
        candidate_theme = counterpart_entry.get(target_key)
        if isinstance(candidate_theme, str) and candidate_theme:
            return candidate_theme
        return None

    def _sync_from_settings(self, *_args) -> None:
        """Syncs the local is_dark property from GSettings."""
        color_scheme = self._settings.get_string("color-scheme")
        self.is_dark = color_scheme == "prefer-dark"

    def _sync_theme_family(self, *_args) -> None:
        """Syncs the local theme_family property based on current GTK theme."""
        current_theme = self._settings.get_string("gtk-theme")
        if not current_theme:
            self.theme_family = "default"
            return
            
        # Try finding in the parsed index map first
        resolved_family = self._theme_family_map.get(current_theme)
        
        # Fallback to primitive split if not tracked by themes.json yet
        if not resolved_family:
            resolved_family = current_theme.split("-")[0].lower()
            
        self.theme_family = resolved_family

    def toggle_mode(self) -> None:
        """Toggles between prefer-dark and prefer-light."""
        self.is_dark = not self.is_dark

    def set_mode(self, mode_enum_ignored=None) -> None:
        pass
