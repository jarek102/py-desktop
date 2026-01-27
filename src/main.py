#!/usr/bin/env python3

import sys
from ctypes import CDLL

import versions
import asyncio
from gi.events import GLibEventLoopPolicy

from App import App

if __name__ == "__main__":
    try:
        CDLL('libgtk4-layer-shell.so')
    except OSError:
        print("Error: 'libgtk4-layer-shell.so' not found. Please ensure gtk4-layer-shell is installed.")
        sys.exit(1)
    asyncio.set_event_loop_policy(GLibEventLoopPolicy())
    app = App()
    app.run(None)