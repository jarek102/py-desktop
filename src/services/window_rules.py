from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any

import kdl

logger = logging.getLogger("py_desktop.window_rules")


@dataclass(frozen=True)
class MatchCriterion:
    app_id: str | None
    title: str | None


@dataclass
class WindowRule:
    matches: list[MatchCriterion]
    workspace: str | None = None
    maximized: bool | None = None
    fullscreen: bool | None = None
    focused: bool | None = None
    width: dict[str, Any] | None = None


_AUTODISCOVER_PATHS: list[str] = [
    "~/.config/niri/cfg/rules.kdl",
    "~/.config/niri/config.kdl",
]


def find_rules_file() -> str | None:
    """Returns the first existing rules file path, or None if none found."""
    for path in _AUTODISCOVER_PATHS:
        expanded = os.path.expanduser(path)
        if os.path.exists(expanded):
            return expanded
    return None


def parse_rules_from_file(path: str) -> list[WindowRule]:
    """
    Parses window-rule nodes from a KDL file.

    KDL schema reference:
      window-rule {
          match app-id="regex" title="regex"   // AND within one match node
          match title="regex"                  // OR between separate match nodes
          open-on-workspace "name"
          open-maximized true|false
          open-fullscreen true|false
          open-focused true|false
          default-column-width { proportion 0.5 }   // child node form
          default-column-width 0.5                  // argument form (raw value)
      }
    """
    rules: list[WindowRule] = []

    if not os.path.exists(path):
        logger.warning("KDL rules file not found at %s", path)
        return rules

    try:
        with open(path, "r", encoding="utf-8") as file_obj:
            doc = kdl.parse(file_obj.read())
    except Exception as exc:
        logger.error("Failed to parse KDL file %s: %s", path, exc)
        return rules

    for node in doc.nodes:
        if node.name != "window-rule":
            continue

        workspace: str | None = None
        maximized: bool | None = None
        fullscreen: bool | None = None
        focused: bool | None = None
        width: dict[str, Any] | None = None
        match_criteria: list[MatchCriterion] = []

        for child in node.nodes:
            match child.name:
                case "open-on-workspace" if child.args:
                    workspace = child.args[0]
                case "open-maximized" if child.args:
                    maximized = child.args[0]
                case "open-fullscreen" if child.args:
                    fullscreen = child.args[0]
                case "open-focused" if child.args:
                    focused = child.args[0]
                case "default-column-width":
                    # KDL schema: default-column-width can be written as either
                    #   default-column-width { proportion 0.5 }   (child node form)
                    #   default-column-width 0.5                  (argument form, raw value)
                    if child.nodes:
                        for sub in child.nodes:
                            if sub.name == "proportion" and sub.args:
                                width = {"type": "proportion", "value": sub.args[0]}
                            elif sub.name == "fixed" and sub.args:
                                width = {"type": "fixed", "value": sub.args[0]}
                    elif child.args:
                        width = child.args[0]
                case "match":
                    match_criteria.append(
                        MatchCriterion(
                            app_id=child.props.get("app-id"),
                            title=child.props.get("title"),
                        )
                    )

        has_any_action = any(
            [
                workspace is not None,
                maximized is not None,
                fullscreen is not None,
                focused is not None,
                width is not None,
            ]
        )

        if has_any_action and match_criteria:
            rules.append(
                WindowRule(
                    matches=match_criteria,
                    workspace=workspace,
                    maximized=maximized,
                    fullscreen=fullscreen,
                    focused=focused,
                    width=width,
                )
            )

    logger.info("Parsed %d window rules from %s", len(rules), path)
    return rules


def match_window(
    rules: list[WindowRule],
    app_id: str,
    title: str,
) -> WindowRule | None:
    """
    Returns the first rule that matches the given app_id and title, or None.

    Each match node within a rule uses AND logic (all criteria must pass).
    Multiple match nodes within a rule use OR logic (any criterion can pass).
    """
    for rule in rules:
        for criterion in rule.matches:
            app_id_ok = (criterion.app_id is None) or bool(
                re.search(criterion.app_id, app_id, re.IGNORECASE)
            )
            title_ok = (criterion.title is None) or bool(
                re.search(criterion.title, title, re.IGNORECASE)
            )
            if app_id_ok and title_ok:
                return rule
    return None
