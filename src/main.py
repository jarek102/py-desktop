#!/usr/bin/env python3

from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')

import versions

from App import App

if __name__ == "__main__":
    app = App()
    app.run(None)