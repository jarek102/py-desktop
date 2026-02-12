#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -lt 2 ]]; then
    echo "Usage: $0 <instance-name> <request...>" >&2
    exit 1
fi

INSTANCE_NAME="$1"
shift

if ! command -v astal >/dev/null 2>&1; then
    echo "error: astal CLI not found in PATH" >&2
    exit 1
fi

exec astal -i "${INSTANCE_NAME}" "$@"
