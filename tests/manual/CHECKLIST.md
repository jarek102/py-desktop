# Manual Verification Checklist

Use this checklist after `just smoke-niri`, `just smoke-scroll`, or `just smoke-hyprland`.

## Safety

- Keep volume low before test start.
- Avoid rapid brightness sweeps/flashing actions.
- Stop test immediately if behavior becomes disruptive.

## Core Startup

- App launches without traceback.
- Bar appears on expected monitor(s).
- `scripts/astal-ipc.sh <instance> ping` returns `pong`.
- `scripts/astal-ipc.sh <instance> status` returns valid JSON.

## Workspace Module

- Workspace buttons render for current output.
- Active workspace has `active` style.
- Clicking a workspace button changes focus.
- Mouse wheel on workspace module switches workspace predictably.

## Device Menu

- Opening/closing device menu works from bar button.
- Overlay closes popup on click outside.
- Logout/reboot/poweroff buttons are visible and not accidentally triggered.

## Audio/Brightness/Bluetooth

- Volume icon updates when changing volume.
- Brightness slider moves and does not spike/flicker.
- Bluetooth list renders and favorite toggle persists.

## Compositor-Specific

### Niri

- Workspace/output mapping matches current Niri output.
- No repeated warnings about missing monitor/output during normal usage.

### Scroll

- Workspace list appears and updates while switching workspaces.
- Focus command via workspace click works.

### Hyprland

- Startup does not crash when monitors/workspaces change.
- No runaway log spam from monitor rebinding.
