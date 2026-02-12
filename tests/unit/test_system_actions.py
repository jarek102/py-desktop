from services import system_actions


def test_reboot_uses_systemctl(monkeypatch):
    captured = {}

    def fake_popen(command):
        captured["command"] = command
        return None

    monkeypatch.setattr(system_actions.subprocess, "Popen", fake_popen)
    system_actions.reboot()

    assert captured["command"] == ["systemctl", "reboot"]


def test_poweroff_uses_systemctl(monkeypatch):
    captured = {}

    def fake_popen(command):
        captured["command"] = command
        return None

    monkeypatch.setattr(system_actions.subprocess, "Popen", fake_popen)
    system_actions.poweroff()

    assert captured["command"] == ["systemctl", "poweroff"]


def test_suspend_uses_systemctl(monkeypatch):
    captured = {}

    def fake_popen(command):
        captured["command"] = command
        return None

    monkeypatch.setattr(system_actions.subprocess, "Popen", fake_popen)
    system_actions.suspend()

    assert captured["command"] == ["systemctl", "suspend"]
