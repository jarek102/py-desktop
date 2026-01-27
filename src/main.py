#!/usr/bin/env python3

import sys
import pathlib
from ctypes import CDLL

try:
    CDLL('libgtk4-layer-shell.so')
except OSError:
    print("Error: 'libgtk4-layer-shell.so' not found. Please ensure gtk4-layer-shell is installed.")
    sys.exit(1)

# Add src directory to sys.path to allow direct imports of modules in src
src_dir = pathlib.Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import versions
import asyncio
from gi.events import GLibEventLoopPolicy

from App import App

if __name__ == "__main__":
    asyncio.set_event_loop_policy(GLibEventLoopPolicy())
    app = App()
    app.run(None)