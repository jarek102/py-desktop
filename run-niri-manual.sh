#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

if ! command -v niri >/dev/null 2>&1; then
    echo "error: niri is not installed or not in PATH" >&2
    exit 1
fi

INSTANCE_NAME="py_desktop_niri_nested_manual"
NIRI_CONFIG_PATH="${ROOT_DIR}/config/niri-nested.kdl"

APP_CMD=(python3 "${ROOT_DIR}/src/main.py" --instance-name "${INSTANCE_NAME}")

NIRI_ARGS=()
if [[ -n "${NIRI_CONFIG_PATH}" ]]; then
    NIRI_ARGS+=(-c "${NIRI_CONFIG_PATH}")
fi

APP_LOG="/tmp/niri_app_manual.log"

echo "Starting nested Niri with instance '${INSTANCE_NAME}'"
echo "App log will be in ${APP_LOG}"
rm -f "${APP_LOG}"

niri "${NIRI_ARGS[@]}" -- sh -lc '
    echo "Nested env WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-unset} NIRI_SOCKET=${NIRI_SOCKET:-unset}"
    cd "'"${ROOT_DIR}"'"
    exec env \
        XDG_CURRENT_DESKTOP=niri \
        XDG_SESSION_TYPE=wayland \
        PYTHONPATH=src \
        "$@" > "'"${APP_LOG}"'" 2>&1
' sh "${APP_CMD[@]}" &
NIRI_PID=$!

echo "Niri started with PID ${NIRI_PID}."
echo "Will wait for 10 seconds and then show the log."
sleep 10
echo "App log:"
cat "${APP_LOG}"
echo "You can now kill the process by running: kill ${NIRI_PID}"