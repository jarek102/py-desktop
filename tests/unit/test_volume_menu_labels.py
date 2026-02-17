from ui.quicksettings.VolumeMenu import VolumeMenu


def test_default_change_triggers_rebind():
    class Dummy:
        called = False

        def bind_default(self):
            self.called = True

    target = Dummy()
    VolumeMenu.on_default_changed(target)
    assert target.called is True