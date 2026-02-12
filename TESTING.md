# Testing Guide

This project uses two complementary testing layers:

1. Automated checks in `tests/` for fast regression coverage.
2. Nested compositor smoke runs for real integration behavior.

## Automated Tests

- Run unit tests:
  - `just test`
- Run quick local gate:
  - `just check`

Current tests live under:
- `tests/unit/`
- `tests/manual/`

## Astal IPC for Non-Interactive Verification

The app supports simple Astal requests:

- `ping` -> `pong`
- `status` -> JSON snapshot with window/popup state
- `toggle-device-menu` -> toggles menu, returns popup/device visibility state
- `close-popups` -> closes active popup

Helper:

- `./scripts/astal-ipc.sh <instance-name> ping`
- `./scripts/astal-ipc.sh <instance-name> status`
- `just smoke-ipc` for automated ping/status check against a live app process
  - also validates device menu open/close via IPC

## Nested Compositor Runs

Each run should use a unique instance name.

### Niri (nested)

- `just smoke-niri`
- `just smoke-niri-ipc` for bounded nested-Niri startup smoke + log checks
- Optional custom config:
  - `PY_DESKTOP_NIRI_CONFIG=/path/to/niri-test.kdl just smoke-niri`
  - default config is `config/niri-nested.kdl`

The script sets:
- `XDG_CURRENT_DESKTOP=niri`
- `XDG_SESSION_TYPE=wayland`
- captures nested `WAYLAND_DISPLAY` and `NIRI_SOCKET` to verify compositor/socket isolation from host
- verifies nested `NIRI_SOCKET` differs from host `NIRI_SOCKET` when host socket exists

### Scroll (nested)

- `just smoke-scroll`
- Optional custom config:
  - `PY_DESKTOP_SCROLL_CONFIG=/path/to/scroll-test.conf just smoke-scroll`
- Optional renderer override (useful on NVIDIA):
  - `PY_DESKTOP_GSK_RENDERER=gl just smoke-scroll`

The script sets:
- `XDG_CURRENT_DESKTOP=scroll`
- `XDG_SESSION_TYPE=wayland`
- `SCROLLSOCK`, `SWAYSOCK`, `I3SOCK` to the nested socket path
- `GSK_RENDERER=gl` by default (override with `PY_DESKTOP_GSK_RENDERER`)
- creates workspaces `2`, `3`, then returns to `1` via `scrollmsg`

Scroll workspace data is currently queried via `scrollmsg` from Python.
Workspace updates are event-driven via `scrollmsg -m -t subscribe`.

Notes:
- Per `man scroll`, Scroll does not accept mixing options and positional command in one call (`scroll -c ... <command>` is invalid).
- On this system, `/proc/<pid>/environ` is restricted; nested display detection is parsed from Scroll startup logs instead.

### Hyprland (current best-effort)

Nested Hyprland is not considered stable here yet.

- Run only from/against an active Hyprland session:
  - `just smoke-hyprland`
- Requires:
  - `HYPRLAND_INSTANCE_SIGNATURE` in environment

## Safety Defaults

Manual smoke tests should avoid disruptive effects:

- No loud sound tests.
- No high-frequency brightness flashing.
- Prefer state checks (workspace changes, menu visibility, IPC status) over stress effects.

See repeatable checklist:

- `tests/manual/CHECKLIST.md`

## Habit For Larger Features

After larger UI/service changes, run this sequence:

1. `just ui`
2. `just check`
3. `just smoke-ipc`
4. `just smoke-niri-ipc`

## Known Environment Caveats

- In this environment, reading Astal power profiles through direct getter APIs can be unstable.
- `PowerProfileService` intentionally reads profile list from `AstalPowerProfiles.get_default().props.profiles`.
