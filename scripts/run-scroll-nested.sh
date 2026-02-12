#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v scroll >/dev/null 2>&1; then
    echo "error: scroll is not installed or not in PATH" >&2
    exit 1
fi

INSTANCE_NAME="${PY_DESKTOP_INSTANCE_NAME:-py_desktop_scroll_nested_${PPID}}"
SCROLL_CONFIG_PATH="${PY_DESKTOP_SCROLL_CONFIG:-config/scroll-nested.conf}"
SCROLL_LOG="${PY_DESKTOP_SCROLL_LOG:-/tmp/${INSTANCE_NAME}.scroll.log}"
APP_LOG="${PY_DESKTOP_SCROLL_APP_LOG:-/tmp/${INSTANCE_NAME}.app.log}"
ENV_CAPTURE="${PY_DESKTOP_SCROLL_ENV_CAPTURE:-/tmp/${INSTANCE_NAME}.env}"
GSK_RENDERER_VALUE="${PY_DESKTOP_GSK_RENDERER:-gl}"

if [[ "$#" -gt 0 ]]; then
    APP_CMD=("$@")
else
    APP_CMD=(python3 src/main.py --instance-name "${INSTANCE_NAME}")
fi

SCROLL_ARGS=()
if [[ -n "${SCROLL_CONFIG_PATH}" ]]; then
    SCROLL_ARGS+=(-c "${SCROLL_CONFIG_PATH}")
fi

RUNTIME_DIR="/run/user/$(id -u)"

echo "Starting nested Scroll with instance '${INSTANCE_NAME}'"
scroll -V "${SCROLL_ARGS[@]}" >"${SCROLL_LOG}" 2>&1 &
SCROLL_PID=$!

if ! kill -0 "${SCROLL_PID}" 2>/dev/null; then
    echo "error: scroll failed to start" >&2
    tail -n 120 "${SCROLL_LOG}" >&2 || true
    exit 1
fi

SCROLL_SOCKET="${RUNTIME_DIR}/scroll-ipc.$(id -u).${SCROLL_PID}.sock"
echo "Waiting for Scroll IPC socket..."
for _ in $(seq 1 80); do
    if [[ -S "${SCROLL_SOCKET}" ]]; then
        break
    fi
    if ! kill -0 "${SCROLL_PID}" 2>/dev/null; then
        echo "error: scroll exited before socket became available" >&2
        tail -n 120 "${SCROLL_LOG}" >&2 || true
        exit 1
    fi
    sleep 0.1
done

if [[ ! -S "${SCROLL_SOCKET}" ]]; then
    echo "error: could not detect Scroll IPC socket at ${SCROLL_SOCKET}" >&2
    tail -n 120 "${SCROLL_LOG}" >&2 || true
    exit 1
fi

echo "Waiting for nested Wayland socket..."
NESTED_WAYLAND=""
for _ in $(seq 1 80); do
    NESTED_WAYLAND="$(sed -n "s/.*Running compositor on wayland display '\\([^']*\\)'.*/\\1/p" "${SCROLL_LOG}" | tail -n1 || true)"
    if [[ -n "${NESTED_WAYLAND}" ]]; then
        break
    fi
    if ! kill -0 "${SCROLL_PID}" 2>/dev/null; then
        echo "error: scroll exited while waiting for WAYLAND_DISPLAY" >&2
        tail -n 120 "${SCROLL_LOG}" >&2 || true
        exit 1
    fi
    sleep 0.1
done

if [[ -z "${NESTED_WAYLAND}" ]]; then
    echo "error: could not detect nested WAYLAND_DISPLAY from scroll logs" >&2
    tail -n 120 "${SCROLL_LOG}" >&2 || true
    exit 1
fi

printf "WAYLAND_DISPLAY=%s\nSCROLLSOCK=%s\nSWAYSOCK=%s\nI3SOCK=%s\nGSK_RENDERER=%s\nSCROLL_PID=%s\nINSTANCE_NAME=%s\n" \
    "${NESTED_WAYLAND}" "${SCROLL_SOCKET}" "${SCROLL_SOCKET}" "${SCROLL_SOCKET}" "${GSK_RENDERER_VALUE}" "${SCROLL_PID}" "${INSTANCE_NAME}" > "${ENV_CAPTURE}"

echo "Nested env:"
cat "${ENV_CAPTURE}"

echo "Launching app..."
env \
    WAYLAND_DISPLAY="${NESTED_WAYLAND}" \
    SCROLLSOCK="${SCROLL_SOCKET}" \
    SWAYSOCK="${SCROLL_SOCKET}" \
    I3SOCK="${SCROLL_SOCKET}" \
    XDG_CURRENT_DESKTOP=scroll \
    XDG_SESSION_TYPE=wayland \
    GSK_RENDERER="${GSK_RENDERER_VALUE}" \
    PYTHONPATH=src \
    "${APP_CMD[@]}" >"${APP_LOG}" 2>&1 &
APP_PID=$!

sleep 1
if ! kill -0 "${APP_PID}" 2>/dev/null; then
    echo "error: app exited quickly; see ${APP_LOG}" >&2
    tail -n 120 "${APP_LOG}" >&2 || true
    exit 1
fi

scrollmsg -s "${SCROLL_SOCKET}" workspace 2 >/dev/null 2>&1 || true
scrollmsg -s "${SCROLL_SOCKET}" workspace 3 >/dev/null 2>&1 || true
scrollmsg -s "${SCROLL_SOCKET}" workspace 1 >/dev/null 2>&1 || true

echo "Started nested Scroll session:"
echo "  scroll pid: ${SCROLL_PID}"
echo "  app pid: ${APP_PID}"
echo "  env capture: ${ENV_CAPTURE}"
echo "  scroll log: ${SCROLL_LOG}"
echo "  app log: ${APP_LOG}"
echo "To stop: kill ${APP_PID} ${SCROLL_PID}"
