from services.theme_service import ThemeMode, ThemeService


class FakeSettings:
    def __init__(self, color_scheme="default"):
        self._color_scheme = color_scheme
        self._handlers = []

    def connect(self, signal, callback):
        self._handlers.append((signal, callback))
        return 1

    def get_string(self, key):
        if key == "color-scheme":
            return self._color_scheme
        return ""

    def set_string(self, key, value):
        if key == "color-scheme":
            self._color_scheme = value
            for signal, callback in self._handlers:
                if signal == "changed::color-scheme":
                    callback()


def test_mode_from_settings_dark():
    service = ThemeService(settings=FakeSettings(color_scheme="prefer-dark"))
    assert service.get_mode() == ThemeMode.DARK
    assert service.is_dark is True


def test_set_mode_dark_writes_expected_value():
    settings = FakeSettings()
    service = ThemeService(settings=settings)
    service.set_mode(ThemeMode.DARK)
    assert settings.get_string("color-scheme") == "prefer-dark"
    assert service.is_dark is True


def test_set_mode_light_writes_expected_value():
    settings = FakeSettings(color_scheme="prefer-dark")
    service = ThemeService(settings=settings)
    service.set_mode(ThemeMode.LIGHT)
    assert settings.get_string("color-scheme") == "default"
    assert service.is_dark is False


def test_toggle_roundtrip():
    settings = FakeSettings(color_scheme="default")
    service = ThemeService(settings=settings)
    assert service.toggle_mode() == ThemeMode.DARK
    assert service.toggle_mode() == ThemeMode.LIGHT
