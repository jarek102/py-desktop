
from typing import Protocol


class WindowManager(Protocol):
    def toggle_menu(self, gdkmonitor=None) -> None:
        raise NotImplementedError