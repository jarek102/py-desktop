from __future__ import annotations

import logging
import os
from typing import Any

import versions
from gi.repository import AstalNiri, Gio, GLib, GObject

from services.window_rules import (
    WindowRule,
    find_rules_file,
    match_window,
    parse_rules_from_file,
)

logger = logging.getLogger("py_desktop.window_organizer")

_DCONF_SCHEMA = "com.github.jarek102.py-desktop"
_DCONF_KEY_ENABLED = "window-organizer-enabled"
_DCONF_KEY_RULES_PATH = "window-rules-path"


class WindowOrganizer(GObject.Object):
    """
    Niri-only reactive window organizer service.

    Listens for new windows via AstalNiri and applies placement rules
    parsed from a KDL file. Integrates into the py-desktop GLib main loop.
    """

    _instance: WindowOrganizer | None = None

    @classmethod
    def get_default(cls) -> WindowOrganizer:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(
        self,
        rules_path_override: str | None = None,
    ) -> None:
        super().__init__()
        # Allow re-entrant calls to get_default() during construction.
        WindowOrganizer._instance = self

        self._settings = Gio.Settings.new(_DCONF_SCHEMA)
        self._rules: list[WindowRule] = []
        self._processed_window_ids: set[int] = set()
        # Map window_id -> (window_obj, handler_id) for late-title-resolving windows
        self._title_watch_handlers: dict[int, tuple[AstalNiri.Window, int]] = {}

        # Note: 'msg' is lowercase intentionally — this matches the AstalNiri Vala class name.
        self._niri_msg = AstalNiri.msg.new()
        self._niri_state = AstalNiri.Niri.get_default()

        self._rules_path_override = rules_path_override

        # React to dconf enabled toggle at runtime
        self._settings.connect(
            f"changed::{_DCONF_KEY_ENABLED}", self._on_enabled_changed
        )
        # React to dconf rules path change at runtime (reload rules)
        self._settings.connect(
            f"changed::{_DCONF_KEY_RULES_PATH}", self._on_rules_path_changed
        )

        if self.enabled:
            self._start()
        else:
            logger.info("WindowOrganizer is disabled via dconf.")

    @property
    def enabled(self) -> bool:
        return self._settings.get_boolean(_DCONF_KEY_ENABLED)

    def _resolve_rules_path(self) -> str | None:
        """
        Priority: CLI override > dconf key > autodiscovery.
        Returns None if no rules file can be found.
        """
        if self._rules_path_override:
            return os.path.expanduser(self._rules_path_override)

        dconf_path = self._settings.get_string(_DCONF_KEY_RULES_PATH)
        if dconf_path:
            return os.path.expanduser(dconf_path)

        return find_rules_file()

    def _start(self) -> None:
        path = self._resolve_rules_path()
        if path is None:
            logger.warning(
                "WindowOrganizer: no rules file found. "
                "Set window-rules-path in dconf or create ~/.config/niri/cfg/rules.kdl"
            )
            return

        self._rules = parse_rules_from_file(path)
        if not self._rules:
            logger.warning(
                "WindowOrganizer: rules file parsed but contained no actionable rules."
            )
            return

        logger.info("WindowOrganizer: loaded %d rules from %s", len(self._rules), path)

        self._niri_state.connect("notify::windows", self._on_windows_changed)
        logger.info("WindowOrganizer: performing initial scan of existing windows...")
        self._on_windows_changed(self._niri_state, None)

    def _stop(self) -> None:
        """Disconnect all signal handlers and clear tracking state."""
        try:
            self._niri_state.disconnect_by_func(self._on_windows_changed)
        except Exception as exc:
            logger.warning(
                "WindowOrganizer: could not disconnect windows handler: %s", exc
            )

        for win_id, (win, handler_id) in list(self._title_watch_handlers.items()):
            try:
                win.disconnect(handler_id)
            except Exception as exc:
                logger.warning(
                    "WindowOrganizer: could not disconnect title handler for window %d: %s",
                    win_id,
                    exc,
                )
        self._title_watch_handlers.clear()
        self._processed_window_ids.clear()
        self._rules = []
        logger.info("WindowOrganizer: stopped.")

    def _on_enabled_changed(self, _settings: Gio.Settings, _key: str) -> None:
        if self.enabled:
            logger.info("WindowOrganizer: enabled via dconf, starting...")
            self._start()
        else:
            logger.info("WindowOrganizer: disabled via dconf, stopping...")
            self._stop()

    def _on_rules_path_changed(self, _settings: Gio.Settings, _key: str) -> None:
        if self.enabled:
            logger.info("WindowOrganizer: rules path changed, reloading...")
            self._stop()
            self._start()

    def _on_windows_changed(
        self, niri_state: AstalNiri.Niri, _param: object
    ) -> None:
        current_windows = niri_state.get_windows()

        if not current_windows:
            for win_id, (win, handler_id) in list(self._title_watch_handlers.items()):
                try:
                    win.disconnect(handler_id)
                except Exception as exc:
                    logger.warning(
                        "WindowOrganizer: could not disconnect handler for window %d: %s",
                        win_id,
                        exc,
                    )
            self._title_watch_handlers.clear()
            self._processed_window_ids.clear()
            return

        current_window_ids = {win.get_id() for win in current_windows}

        # Clean up closed windows
        closed_ids = self._processed_window_ids - current_window_ids
        if closed_ids:
            self._processed_window_ids.difference_update(closed_ids)
            for win_id in closed_ids:
                if win_id in self._title_watch_handlers:
                    win, handler_id = self._title_watch_handlers.pop(win_id)
                    try:
                        win.disconnect(handler_id)
                    except Exception as exc:
                        logger.warning(
                            "WindowOrganizer: could not disconnect handler for closed window %d: %s",
                            win_id,
                            exc,
                        )

        # Process new windows
        new_windows = [
            win
            for win in current_windows
            if win.get_id() not in self._processed_window_ids
        ]

        for window in new_windows:
            win_id = window.get_id()
            app_id = window.get_app_id() or ""

            # Mark as seen immediately to prevent duplicate processing on
            # re-entrant notify::windows signals before this loop completes.
            self._processed_window_ids.add(win_id)

            # Apps that update their title asynchronously after the window
            # is first reported (e.g. Firefox) need a title-change watcher.
            if self._needs_title_watch(app_id):
                handler_id = window.connect("notify::title", self._on_window_title_changed)
                self._title_watch_handlers[win_id] = (window, handler_id)
                # Try immediately in case the title is already set.
                if self._apply_rules(window):
                    self._remove_title_watch(window)
            else:
                self._apply_rules(window)

    def _on_window_title_changed(
        self, window: AstalNiri.Window, _param: object
    ) -> None:
        if self._apply_rules(window):
            self._remove_title_watch(window)

    def _needs_title_watch(self, app_id: str) -> bool:
        """Returns True for apps known to update their title after window creation."""
        return "firefox" in app_id.lower()

    def _remove_title_watch(self, window: AstalNiri.Window) -> None:
        win_id = window.get_id()
        if win_id in self._title_watch_handlers:
            _, handler_id = self._title_watch_handlers.pop(win_id)
            try:
                window.disconnect(handler_id)
            except Exception as exc:
                logger.warning(
                    "WindowOrganizer: could not disconnect title watch for window %d: %s",
                    win_id,
                    exc,
                )

    def _apply_rules(self, window: AstalNiri.Window) -> bool:
        """
        Applies the first matching rule to window. Returns True if a rule matched.

        A rule is considered matched even if all its actions are already satisfied
        (e.g. window is already on the target workspace). The return value is used
        to decide whether to stop watching the window's title for late matches.
        """
        win_id = window.get_id()
        win_title = window.get_title() or ""
        win_app_id = window.get_app_id() or ""

        rule = match_window(self._rules, win_app_id, win_title)
        if rule is None:
            return False

        # Determine which actions are actually needed
        ws_already_correct = False
        if rule.workspace:
            current_ws = window.get_workspace()
            if current_ws and current_ws.get_name() == rule.workspace:
                ws_already_correct = True

        should_move = bool(rule.workspace) and not ws_already_correct
        should_maximize = rule.maximized
        should_fullscreen = rule.fullscreen
        should_focus = rule.focused
        target_width = rule.width

        if not any(
            [should_move, should_maximize, should_fullscreen, should_focus, target_width]
        ):
            logger.debug(
                "WindowOrganizer: Win:%d (%s / %s) matched rule but all actions already satisfied.",
                win_id,
                win_app_id,
                win_title,
            )
            return True

        actions: list[str] = []
        if should_move:
            actions.append(f"move -> '{rule.workspace}'")
        if should_maximize:
            actions.append("maximize")
        if should_fullscreen:
            actions.append("fullscreen")
        if should_focus:
            actions.append("focus")
        if target_width:
            actions.append(f"width -> {target_width}")

        logger.info(
            "WindowOrganizer: Win:%d (app_id='%s', title='%s') : %s",
            win_id,
            win_app_id,
            win_title,
            ", ".join(actions),
        )

        if should_move:
            self._niri_msg.move_window_to_workspace_by_name(
                window_id=GLib.Variant.new_int64(win_id),
                workspace_name=rule.workspace,
                focus=False,
            )

        if should_maximize:
            result = self._niri_msg.set_window_width_set_proportion(
                GLib.Variant.new_int64(win_id), 100.0
            )
            logger.debug("WindowOrganizer: maximize result: %s", result)

        if should_fullscreen:
            result = self._niri_msg.fullscreen_window(GLib.Variant.new_int64(win_id))
            logger.debug("WindowOrganizer: fullscreen result: %s", result)

        if target_width:
            self._apply_width(win_id, target_width)

        if should_focus:
            # Only steal focus if the window landed on the already-focused workspace,
            # to avoid jumping the user's view to a different workspace.
            focused_ws = self._niri_state.get_focused_workspace()
            window_ws = window.get_workspace()
            if not should_move or (
                focused_ws is not None
                and window_ws is not None
                and focused_ws.get_id() == window_ws.get_id()
            ):
                result = self._niri_msg.focus_window(GLib.Variant.new_int64(win_id))
                logger.debug("WindowOrganizer: focus result: %s", result)

        return True

    def _apply_width(self, win_id: int, target_width: dict[str, Any]) -> None:
        try:
            match target_width["type"]:
                case "proportion":
                    percent = float(target_width["value"]) * 100.0
                    result = self._niri_msg.set_window_width_set_proportion(
                        GLib.Variant.new_int64(win_id), percent
                    )
                    logger.debug("WindowOrganizer: set width proportion result: %s", result)
                case "fixed":
                    result = self._niri_msg.set_window_width_set_fixed(
                        GLib.Variant.new_int64(win_id), int(target_width["value"])
                    )
                    logger.debug("WindowOrganizer: set width fixed result: %s", result)
        except Exception as exc:
            logger.error("WindowOrganizer: failed to set window width: %s", exc)
