#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

INSTANCE_NAME="${PY_DESKTOP_INSTANCE_NAME:-py_desktop_hypr_test_${PPID}}"

if [[ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
    echo "warning: HYPRLAND_INSTANCE_SIGNATURE is not set." >&2
    echo "Run this in an active Hyprland session or export the target signature first." >&2
    exit 1
fi

if [[ "$#" -gt 0 ]]; then
    APP_CMD=("$@")
else
    APP_CMD=(python3 src/main.py --instance-name "${INSTANCE_NAME}")
fi

echo "Starting app against Hyprland instance '${HYPRLAND_INSTANCE_SIGNATURE}'"
exec env \
    XDG_CURRENT_DESKTOP=hyprland \
    XDG_SESSION_TYPE=wayland \
    PYTHONPATH=src \
    "${APP_CMD[@]}"
