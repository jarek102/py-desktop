#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v niri >/dev/null 2>&1; then
    echo "error: niri is not installed or not in PATH" >&2
    exit 1
fi

INSTANCE_NAME="${PY_DESKTOP_INSTANCE_NAME:-py_desktop_niri_smoke_${PPID}}"
NIRI_CONFIG_PATH="${PY_DESKTOP_NIRI_CONFIG:-config/niri-nested.kdl}"
SMOKE_TIMEOUT="${PY_DESKTOP_NIRI_SMOKE_TIMEOUT:-18s}"
SMOKE_LOG="${PY_DESKTOP_NIRI_SMOKE_LOG:-/tmp/py-desktop-niri-smoke-${INSTANCE_NAME}.log}"
ENV_CAPTURE="${PY_DESKTOP_NIRI_ENV_CAPTURE:-/tmp/py-desktop-niri-env-${INSTANCE_NAME}.log}"
HOST_NIRI_SOCKET="${NIRI_SOCKET:-}"

NIRI_ARGS=()
if [[ -n "${NIRI_CONFIG_PATH}" ]]; then
    NIRI_ARGS+=(-c "${NIRI_CONFIG_PATH}")
fi

echo "Running nested Niri smoke for instance '${INSTANCE_NAME}' (timeout ${SMOKE_TIMEOUT})"
set +e
timeout "${SMOKE_TIMEOUT}" niri "${NIRI_ARGS[@]}" -- env \
    XDG_CURRENT_DESKTOP=niri \
    XDG_SESSION_TYPE=wayland \
    PYTHONPATH=src \
    sh -lc 'printf "WAYLAND_DISPLAY=%s\nNIRI_SOCKET=%s\n" "${WAYLAND_DISPLAY:-}" "${NIRI_SOCKET:-}" > "$1"; exec python3 src/main.py --instance-name "$2"' sh "${ENV_CAPTURE}" "${INSTANCE_NAME}" >"${SMOKE_LOG}" 2>&1
RC=$?
set -e

# timeout exit is expected for a bounded smoke run
if [[ "${RC}" -ne 0 && "${RC}" -ne 124 ]]; then
    echo "error: nested niri smoke exited with unexpected status ${RC}" >&2
    tail -n 120 "${SMOKE_LOG}" >&2 || true
    exit "${RC}"
fi

if rg -q "Gtk-WARNING .*duplicate child name|SIGSEGV|terminated by signal SIGSEGV" "${SMOKE_LOG}"; then
    echo "error: nested niri smoke found critical warnings/crashes" >&2
    rg -n "Gtk-WARNING|duplicate child name|SIGSEGV|terminated by signal" "${SMOKE_LOG}" >&2 || true
    exit 1
fi

if [[ ! -s "${ENV_CAPTURE}" ]]; then
    echo "error: nested env capture is missing (${ENV_CAPTURE})" >&2
    exit 1
fi

NESTED_WAYLAND_DISPLAY="$(awk -F= '/^WAYLAND_DISPLAY=/{print $2}' "${ENV_CAPTURE}" | head -n1)"
NESTED_NIRI_SOCKET="$(awk -F= '/^NIRI_SOCKET=/{print $2}' "${ENV_CAPTURE}" | head -n1)"

if [[ -z "${NESTED_WAYLAND_DISPLAY}" || -z "${NESTED_NIRI_SOCKET}" ]]; then
    echo "error: nested env is incomplete:" >&2
    cat "${ENV_CAPTURE}" >&2
    exit 1
fi

if [[ -n "${HOST_NIRI_SOCKET}" && "${HOST_NIRI_SOCKET}" == "${NESTED_NIRI_SOCKET}" ]]; then
    echo "error: nested niri socket matches host socket; environment isolation failed" >&2
    echo "host=${HOST_NIRI_SOCKET}" >&2
    echo "nested=${NESTED_NIRI_SOCKET}" >&2
    exit 1
fi

echo "Nested niri smoke passed (no duplicate-child warning / no segfault)"
