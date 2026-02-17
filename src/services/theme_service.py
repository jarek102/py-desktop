from __future__ import annotations
import logging

_log = logging.getLogger(__name__)

import versions
from gi.repository import Gio, GObject



class ThemeService(GObject.Object):
    _is_dark = False

    def __init__(self, settings: Gio.Settings | None = None):
        super().__init__()
        self._settings = settings or Gio.Settings.new("org.gnome.desktop.interface")

        self._settings.connect("changed::color-scheme", self._sync_from_settings)
        self._sync_from_settings()

    @GObject.Property(type=bool, default=False)
    def is_dark(self):
        return self._is_dark

    @is_dark.setter
    def is_dark(self, value: bool):
        self._is_dark = value
        
        # When written to from Python (e.g. binding), update settings.
        # Avoid infinite loops if this was triggered by _sync_from_settings
        color_scheme = self._settings.get_string("color-scheme")
        current_is_settings_dark = color_scheme == "prefer-dark"
        

        if value == current_is_settings_dark:
            return

        # Attempt to trigger screen transition to hide the repaint
        try:
            from services.Compositor import Compositor
            _log.debug("Triggering Niri screen transition for theme switch")
            # Delay in ms to allow apps to repaint behind the frozen screen
            Compositor.get_default().do_screen_transition(500)
        except Exception as e:
            _log.warning(f"Failed to trigger screen transition: {e}")

        new_scheme = "prefer-dark" if value else "prefer-light"
        self._settings.set_string("color-scheme", new_scheme)
        
        # TODO: Re-enable GTK theme switching later. 
        # Currently it breaks with complex theme names or when switching rapidly.
        # current_theme = self._settings.get_string("gtk-theme")
        # new_theme = self._get_next_gtk_theme(current_theme, value)
        # if new_theme != current_theme:
        #      self._settings.set_string("gtk-theme", new_theme)

    def _sync_from_settings(self, *_args) -> None:
        """Syncs the local is_dark property from GSettings."""
        color_scheme = self._settings.get_string("color-scheme")
        # Strict toggle: Only "prefer-dark" is True. "prefer-light", "default", etc. are False.
        self.is_dark = color_scheme == "prefer-dark"

    def _get_next_gtk_theme(self, current_theme: str, target_dark: bool) -> str:
        """Calculates the next GTK theme name based on target state."""
        if target_dark:
            # If we want dark, ensure it ends with -dark
            if not current_theme.endswith("-dark"):
                return f"{current_theme}-dark"
            return current_theme
        else:
            # If we want light, ensure it does NOT end with -dark
            if current_theme.endswith("-dark"):
                return current_theme[:-5]
            return current_theme

    def toggle_mode(self) -> None:
        """Toggles between prefer-dark and prefer-light."""
        # Calculate target state
        self.is_dark = not self.is_dark

    def set_mode(self, mode_enum_ignored=None) -> None:
        pass

