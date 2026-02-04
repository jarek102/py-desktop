#!/usr/bin/env python3

import argparse
import logging
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

def configure_logging():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level.",
    )
    parser.add_argument(
        "--no-logging",
        action="store_true",
        help="Disable logging output.",
    )
    args, _unknown = parser.parse_known_args()

    if args.no_logging:
        logging.disable(logging.CRITICAL)
        return

    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    else:
        logging.getLogger().setLevel(getattr(logging, args.log_level))

    return


from App import App

def loop_step(loop):
    loop.call_soon(loop.stop)
    loop.run_forever()
    return True

if __name__ == "__main__":
    configure_logging()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    GLib.timeout_add(10, loop_step, loop)

    app = App()
    app.acquire_socket()
    sys.exit(app.run(None))
