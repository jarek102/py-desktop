from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger("py_desktop.scroll_ipc")


@dataclass(frozen=True)
class ScrollOutput:
    name: str
    focused: bool


@dataclass(frozen=True)
class ScrollWorkspace:
    num: int
    name: str
    output: str | None
    focused: bool
    visible: bool


def parse_outputs(payload: str) -> list[ScrollOutput]:
    data = json.loads(payload)
    result = []
    for item in data:
        name = item.get("name")
        if not name:
            continue
        result.append(
            ScrollOutput(
                name=str(name),
                focused=bool(item.get("focused", False)),
            )
        )
    return result


def parse_workspaces(payload: str) -> list[ScrollWorkspace]:
    data = json.loads(payload)
    result = []
    for item in data:
        num = int(item.get("num", 0))
        name = str(item.get("name", num))
        output = item.get("output")
        result.append(
            ScrollWorkspace(
                num=num,
                name=name,
                output=str(output) if output is not None else None,
                focused=bool(item.get("focused", False)),
                visible=bool(item.get("visible", False)),
            )
        )
    return result


class ScrollIPC:
    def __init__(self) -> None:
        self._socket = os.environ.get("SWAYSOCK") or os.environ.get("SCROLLSOCK")
        self._monitor_proc: subprocess.Popen[str] | None = None
        self._monitor_thread: threading.Thread | None = None

    def _run(self, msg_type: str, message: str | None = None) -> str:
        command = ["scrollmsg", "-r", "-t", msg_type]
        if self._socket:
            command.extend(["-s", self._socket])
        if message:
            command.append(message)

        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "scrollmsg failed")
        return proc.stdout

    def get_outputs(self) -> list[ScrollOutput]:
        return parse_outputs(self._run("get_outputs"))

    def get_workspaces(self) -> list[ScrollWorkspace]:
        return parse_workspaces(self._run("get_workspaces"))

    def focus_workspace(self, workspace: ScrollWorkspace) -> bool:
        # "workspace <name>" is sway-compatible and works for numbered and named workspaces.
        try:
            self._run("command", f"workspace {workspace.name}")
            return True
        except RuntimeError as err:
            logger.warning("Failed to focus Scroll workspace %s: %s", workspace.name, err)
            return False

    def quit(self) -> bool:
        try:
            self._run("command", "exit")
            return True
        except RuntimeError as err:
            logger.warning("Failed to quit Scroll: %s", err)
            return False

    def start_event_monitor(self, on_event: Callable[[], None]) -> None:
        if self._monitor_proc is not None and self._monitor_proc.poll() is None:
            return

        command = [
            "scrollmsg",
            "-m",
            "-r",
            "-t",
            "subscribe",
            "[\"workspace\",\"output\"]",
        ]
        if self._socket:
            command.extend(["-s", self._socket])

        self._monitor_proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

        def worker() -> None:
            proc = self._monitor_proc
            if proc is None or proc.stdout is None:
                return
            for line in proc.stdout:
                if not line.strip():
                    continue
                try:
                    event_payload = json.loads(line)
                    if isinstance(event_payload, dict) and event_payload.get("success") is True:
                        continue
                except Exception:
                    # keep going on malformed line
                    pass
                on_event()

        self._monitor_thread = threading.Thread(
            target=worker,
            name="scroll-ipc-monitor",
            daemon=True,
        )
        self._monitor_thread.start()

    def stop_event_monitor(self) -> None:
        proc = self._monitor_proc
        if proc is None:
            return
        if proc.poll() is None:
            proc.terminate()
        self._monitor_proc = None
