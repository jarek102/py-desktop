import subprocess


def _run_systemctl(action: str) -> None:
    subprocess.Popen(["systemctl", action])


def reboot() -> None:
    _run_systemctl("reboot")


def poweroff() -> None:
    _run_systemctl("poweroff")


def suspend() -> None:
    _run_systemctl("suspend")
