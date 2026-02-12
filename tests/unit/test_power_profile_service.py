from services.power_profile_service import PowerProfileService, normalize_profiles


class DummyProfile:
    def __init__(self, name):
        self.profile = name


class DummyPowerProfiles:
    def __init__(self, active="balanced", profiles=None):
        self._profiles = profiles or [
            DummyProfile("power-saver"),
            DummyProfile("balanced"),
            DummyProfile("performance"),
        ]
        self.props = type(
            "Props",
            (),
            {
                "active_profile": active,
                "profiles": self._profiles,
            },
        )()
        self.set_calls = []

    def connect(self, *_args):
        return 1

    def get_profiles(self):
        return self._profiles

    def set_active_profile(self, profile):
        self.props.active_profile = profile
        self.set_calls.append(profile)


class DummyBattery:
    def __init__(self, is_present):
        self.props = type("Props", (), {"is_present": is_present})()

    def connect(self, *_args):
        return 1


def test_normalize_profiles_order():
    profiles = [DummyProfile("performance"), DummyProfile("balanced")]
    assert normalize_profiles(profiles) == ["balanced", "performance"]


def test_visible_false_when_battery_absent():
    service = PowerProfileService(
        powerprofiles=DummyPowerProfiles(),
        battery=DummyBattery(is_present=False),
    )
    assert service.visible is False


def test_visible_true_when_battery_present():
    service = PowerProfileService(
        powerprofiles=DummyPowerProfiles(),
        battery=DummyBattery(is_present=True),
    )
    assert service.visible is True


def test_set_profile_calls_backend():
    backend = DummyPowerProfiles()
    service = PowerProfileService(
        powerprofiles=backend,
        battery=DummyBattery(is_present=True),
    )
    assert service.set_profile("performance") is True
    assert backend.set_calls[-1] == "performance"


def test_invalid_profile_is_rejected():
    backend = DummyPowerProfiles()
    service = PowerProfileService(
        powerprofiles=backend,
        battery=DummyBattery(is_present=True),
    )
    assert service.set_profile("invalid-profile") is False
