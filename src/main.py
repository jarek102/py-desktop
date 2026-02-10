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

def parse_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v: WARNING, -vv: INFO, -vvv: DEBUG).",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except for critical errors.",
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    parser.add_argument(
        "-i", "--instance-name",
        default="py_desktop",
        help="Set application instance name.",
    )
    args, _unknown = parser.parse_known_args()
    return args

def configure_logging(args):
    log_level = logging.ERROR

    if args.log_level:
        log_level = getattr(logging, args.log_level)
    elif args.debug:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.CRITICAL
    elif args.verbose > 0:
        if args.verbose == 1:
            log_level = logging.WARNING
        elif args.verbose == 2:
            log_level = logging.INFO
        else:
            log_level = logging.DEBUG

    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    else:
        logging.getLogger().setLevel(log_level)


from App import App

def loop_step(loop):
    loop.call_soon(loop.stop)
    loop.run_forever()
    return True

if __name__ == "__main__":
    args = parse_args()
    configure_logging(args)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    GLib.timeout_add(10, loop_step, loop)

    app = App(instance_name=args.instance_name)
    app.acquire_socket()
    sys.exit(app.run(None))
