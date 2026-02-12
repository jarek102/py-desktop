#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v astal >/dev/null 2>&1; then
    echo "error: astal CLI not found in PATH" >&2
    exit 1
fi

INSTANCE_NAME="${PY_DESKTOP_INSTANCE_NAME:-py_desktop_smoke_${PPID}}"
LOG_FILE="${PY_DESKTOP_SMOKE_LOG:-/tmp/py-desktop-smoke-${INSTANCE_NAME}.log}"
ASTAL_CALL_TIMEOUT="${PY_DESKTOP_ASTAL_TIMEOUT:-2s}"

if [[ "$#" -gt 0 ]]; then
    APP_CMD=("$@")
else
    APP_CMD=(python3 src/main.py --instance-name "${INSTANCE_NAME}")
fi

echo "Starting smoke app instance '${INSTANCE_NAME}'"
"${APP_CMD[@]}" >"${LOG_FILE}" 2>&1 &
APP_PID="$!"

cleanup() {
    timeout "${ASTAL_CALL_TIMEOUT}" astal -i "${INSTANCE_NAME}" -q >/dev/null 2>&1 || true
    if kill -0 "${APP_PID}" >/dev/null 2>&1; then
        kill "${APP_PID}" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

READY=0
for _ in $(seq 1 60); do
    if OUTPUT="$(timeout "${ASTAL_CALL_TIMEOUT}" astal -i "${INSTANCE_NAME}" ping 2>/dev/null)" && [[ "${OUTPUT}" == "pong" ]]; then
        READY=1
        break
    fi
    sleep 0.2
done

if [[ "${READY}" -ne 1 ]]; then
    echo "error: app did not become ready for IPC" >&2
    echo "--- recent log ---" >&2
    tail -n 60 "${LOG_FILE}" >&2 || true
    exit 1
fi

STATUS_JSON="$(timeout "${ASTAL_CALL_TIMEOUT}" astal -i "${INSTANCE_NAME}" status)"
echo "IPC status: ${STATUS_JSON}"

if command -v jq >/dev/null 2>&1; then
    echo "${STATUS_JSON}" | jq -e '.instance_name and (.bars|type=="number") and (.popup_open|type=="boolean")' >/dev/null
fi

# Deeper runtime check: open and close device menu via IPC.
TOGGLE_OPEN="$(timeout "${ASTAL_CALL_TIMEOUT}" astal -i "${INSTANCE_NAME}" toggle-device-menu)"
if command -v jq >/dev/null 2>&1; then
    echo "${TOGGLE_OPEN}" | jq -e '.device_menu_visible == true' >/dev/null
fi

TOGGLE_CLOSE="$(timeout "${ASTAL_CALL_TIMEOUT}" astal -i "${INSTANCE_NAME}" toggle-device-menu)"
if command -v jq >/dev/null 2>&1; then
    echo "${TOGGLE_CLOSE}" | jq -e '.device_menu_visible == false' >/dev/null
fi

echo "Smoke IPC check passed"
