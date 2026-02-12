#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v niri >/dev/null 2>&1; then
    echo "error: niri is not installed or not in PATH" >&2
    exit 1
fi

INSTANCE_NAME="${PY_DESKTOP_INSTANCE_NAME:-py_desktop_niri_nested_${PPID}}"
NIRI_CONFIG_PATH="${PY_DESKTOP_NIRI_CONFIG:-config/niri-nested.kdl}"

if [[ "$#" -gt 0 ]]; then
    APP_CMD=("$@")
else
    APP_CMD=(python3 src/main.py --instance-name "${INSTANCE_NAME}")
fi

NIRI_ARGS=()
if [[ -n "${NIRI_CONFIG_PATH}" ]]; then
    NIRI_ARGS+=(-c "${NIRI_CONFIG_PATH}")
fi

echo "Starting nested Niri with instance '${INSTANCE_NAME}'"
exec niri "${NIRI_ARGS[@]}" -- sh -lc '
    echo "Nested env WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-unset} NIRI_SOCKET=${NIRI_SOCKET:-unset}"
    exec env \
        XDG_CURRENT_DESKTOP=niri \
        XDG_SESSION_TYPE=wayland \
        PYTHONPATH=src \
        "$@"
' sh "${APP_CMD[@]}"
