#!/usr/bin/env python3

from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')

import versions
import asyncio
from gi.events import GLibEventLoopPolicy

from App import App

if __name__ == "__main__":
    asyncio.set_event_loop_policy(GLibEventLoopPolicy())
    app = App()
    app.run(None)