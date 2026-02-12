from ui.quicksettings.VolumeMenu import VolumeMenu, format_active_device_label


def test_format_active_device_label_speaker():
    assert (
        format_active_device_label("speaker", "Built-in Audio")
        == "Speakers: Built-in Audio"
    )


def test_format_active_device_label_microphone():
    assert (
        format_active_device_label("microphone", "Webcam Mic")
        == "Microphone: Webcam Mic"
    )


def test_format_active_device_label_empty_description():
    assert format_active_device_label("speaker", "") == "Speakers: Unknown"


def test_default_change_triggers_rebind():
    class Dummy:
        called = False

        def bind_default(self):
            self.called = True

    target = Dummy()
    VolumeMenu.on_default_changed(target)
    assert target.called is True
