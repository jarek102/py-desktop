#!/usr/bin/env python3

import sys
from ctypes import CDLL

try:
    CDLL('libgtk4-layer-shell.so')
except OSError:
    print("Error: 'libgtk4-layer-shell.so' not found. Please ensure gtk4-layer-shell is installed.")
    sys.exit(1)

import versions
import asyncio
from gi.repository import GLib

from App import App

def loop_step(loop):
    loop.call_soon(loop.stop)
    loop.run_forever()
    return True

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    GLib.timeout_add(10, loop_step, loop)

    app = App()
    sys.exit(app.run(None))