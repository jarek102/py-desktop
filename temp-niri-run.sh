#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # Corrected ROOT_DIR
cd "${ROOT_DIR}"

if ! command -v niri >/dev/null 2>&1; then
    echo "error: niri is not installed or not in PATH" >&2
    exit 1
fi

INSTANCE_NAME="${PY_DESKTOP_INSTANCE_NAME:-py_desktop_niri_nested_${PPID}}"
NIRI_CONFIG_PATH="${ROOT_DIR}/config/niri-nested.kdl"

APP_CMD=(python3 "${ROOT_DIR}/src/test.py" --instance-name "${INSTANCE_NAME}")

NIRI_ARGS=()
if [[ -n "${NIRI_CONFIG_PATH}" ]]; then
    NIRI_ARGS+=(-c "${NIRI_CONFIG_PATH}")
fi

echo "Starting nested Niri with instance '${INSTANCE_NAME}'"
niri "${NIRI_ARGS[@]}" -- sh -lc '
    echo "Nested env WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-unset} NIRI_SOCKET=${NIRI_SOCKET:-unset}"
    cd "'""${ROOT_DIR}""'"
    exec env \
        WAYLAND_DEBUG=1 \
        XDG_CURRENT_DESKTOP=niri \
        XDG_SESSION_TYPE=wayland \
        PYTHONPATH=src \
        "$@" > /tmp/niri_app.log 2>&1
' sh "${APP_CMD[@]}" &
NIRI_PID=$!

echo "Niri started with PID ${NIRI_PID}"
sleep 5
echo "Niri app log:"
cat /tmp/niri_app.log
echo "Killing niri"
kill ${NIRI_PID}
# Just in case it did not die
sleep 1
kill -9 ${NIRI_PID} 2>/dev/null || true
