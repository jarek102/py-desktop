from services.BrightnessService import (
    clamp_internal_percent,
    is_internal_connector,
    should_skip_ddc_display,
)


def test_internal_connector_detection():
    assert is_internal_connector("eDP-1") is True
    assert is_internal_connector("LVDS-1") is True
    assert is_internal_connector("DSI-1") is True
    assert is_internal_connector("HDMI-A-1") is False


def test_should_skip_ddc_internal_when_sysfs_exists():
    assert should_skip_ddc_display("eDP-1", has_sysfs_internal=True) is True


def test_should_not_skip_ddc_when_no_sysfs_internal():
    assert should_skip_ddc_display("eDP-1", has_sysfs_internal=False) is False


def test_internal_clamp_min_floor():
    assert clamp_internal_percent(0) == 1
    assert clamp_internal_percent(1) == 1
    assert clamp_internal_percent(20) == 20
