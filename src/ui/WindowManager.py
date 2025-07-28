
from typing import Protocol


class WindowManager(Protocol):
    def toggle_device_menu(self, gdkmonitor=None) -> None:
        raise NotImplementedError