from __future__ import annotations

import logging

import versions
from gi.repository import AstalBattery, AstalPowerProfiles, GObject

logger = logging.getLogger("py_desktop.power_profiles")

PROFILE_ORDER = ["power-saver", "balanced", "performance"]


def normalize_profiles(raw_profiles) -> list[str]:
    names = []
    if raw_profiles is None:
        return []

    for profile in raw_profiles:
        name = None
        try:
            name = str(getattr(profile, "profile", ""))
        except Exception:
            name = ""
        if not name:
            try:
                props = getattr(profile, "props", None)
                if props is not None:
                    name = str(getattr(props, "profile", ""))
            except Exception:
                name = ""
        if name:
            names.append(name)

    ordered = [name for name in PROFILE_ORDER if name in names]
    extras = [name for name in names if name not in ordered]
    return ordered + extras


class PowerProfileService(GObject.Object):
    visible = GObject.Property(type=bool, default=False)
    active_profile = GObject.Property(type=str, default="balanced")

    def __init__(
        self,
        powerprofiles=None,
        battery=None,
    ):
        super().__init__()
        self._powerprofiles = powerprofiles or AstalPowerProfiles.get_default()
        self._battery = battery or AstalBattery.get_default()
        self.available_profiles: list[str] = []

        self._powerprofiles.connect(
            "notify::active-profile", self._on_active_profile_changed
        )
        self._battery.connect("notify::is-present", self._on_battery_changed)
        self.refresh()

    def _on_active_profile_changed(self, *_args):
        self.refresh_active_profile()

    def _on_battery_changed(self, *_args):
        self.visible = bool(getattr(self._battery.props, "is_present", False))

    def refresh_active_profile(self):
        profile = str(getattr(self._powerprofiles.props, "active_profile", "balanced"))
        if profile:
            self.active_profile = profile

    def refresh(self):
        self.visible = bool(getattr(self._battery.props, "is_present", False))
        try:
            profiles = getattr(self._powerprofiles.props, "profiles", [])
        except Exception:
            profiles = []
        self.available_profiles = normalize_profiles(profiles)
        self.refresh_active_profile()

    def set_profile(self, profile: str) -> bool:
        if not profile:
            return False
        if self.available_profiles and profile not in self.available_profiles:
            return False
        try:
            self._powerprofiles.set_active_profile(profile)
            self.active_profile = profile
            return True
        except Exception as error:
            logger.warning("Failed to set power profile %s: %s", profile, error)
            return False

    def cycle_profile(self) -> str:
        profiles = self.available_profiles or PROFILE_ORDER
        current = self.active_profile if self.active_profile in profiles else profiles[0]
        idx = profiles.index(current)
        target = profiles[(idx + 1) % len(profiles)]
        self.set_profile(target)
        return target
