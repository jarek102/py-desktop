# py-desktop UI Design Specification

> Reference document for all UI implementation work.
> Update when decisions change — note the reason and date.

---

## Design Principles

- **Follow Libadwaita color tokens.** Never hardcode colors. Use `@accent_color`,
  `@card_bg_color`, `@window_bg_color`, `@headerbar_bg_color`, etc. GTK themes
  that implement the Adwaita color contract work automatically.
- **Custom CSS only for geometry.** SCSS handles layout dimensions, spacing
  variables, and shell-specific shapes (pill, panel). Not colors, not states.
- **Blur-ready from day one.** All shell windows use semi-transparent backgrounds
  with solid fallbacks. When niri blur lands, enabling it is a niri config
  change + one SCSS variable change, not a layout rework.
- **Touch targets minimum 44px.** All interactive elements meet this on both
  desktop and laptop profiles.
- **Sparse is fine.** Empty grid cells are acceptable. Never cram things in to
  fill space.

---

## Design Tokens (SCSS)

```scss
// Layout
$panel-width: 456px;        // 6 × 64px tiles + 5 × 8px gaps + 2 × 16px padding
$tile-size: 64px;           // toggle grid cells, square
$tile-gap: 8px;             // gutter between tiles
$bar-height: 36px;          // matches typical GTK headerbar height
$section-gap: 12px;         // vertical spacing between panel sections
$panel-padding: 16px;       // horizontal padding inside panels

// Radii
$radius: 12px;              // panels, cards, DeviceMenu window
$radius-sm: 8px;            // items within panels, rows
$radius-pill: 99px;         // bar pill, OSD, status indicators
$radius-tile: 10px;         // toggle tiles

// Blur (values used when niri blur is active)
$blur-radius: 20px;         // referenced in niri window rules comment, not CSS
$bar-bg-opacity: 0.85;      // solid fallback; reduce when blur active
$panel-bg-opacity: 0.92;

// Spacing (vertical rhythm)
$spacing: 12px;             // primary spacing unit
$spacing-sm: 6px;           // compact groups
$spacing-xs: 4px;           // inline icon/label gaps
```

---

## Color Usage

| Element | Token |
|---------|-------|
| Bar background | `@headerbar_bg_color` at `$bar-bg-opacity` |
| Panel / DeviceMenu background | `@card_bg_color` at `$panel-bg-opacity` |
| Panel row background | `@card_bg_color` |
| Tile inactive | `@card_bg_color` |
| Tile active | `@accent_bg_color` |
| Tile active icon | `@accent_fg_color` |
| Low battery / warning | `@warning_color` |
| Error / critical | `@error_color` |
| Text primary | `@window_fg_color` |
| Text secondary / captions | `@dim_label_color` |
| Separator | `@borders` |

---

## Bar

### Structure

Three zones in a `CenterBox`:

```
┌──────────────────────────────────────────────────────────────────┐
│ [launcher][workspaces]  │  [clock][badge][media][tray]  │  [pill]│
│ ←    left zone    →     │  ←       center zone     →    │ ← right│
└──────────────────────────────────────────────────────────────────┘
```

Height: `$bar-height` (36px).
Background: `@headerbar_bg_color` semi-transparent, blur-ready.

---

### Left Zone — Workspace & App Management

**Contents (left to right):**
- App launcher button (single icon button)
- Workspace group indicator + per-monitor workspace dots

**Workspace display:**
- Group name label (e.g. "dev") in muted style
- Dot row showing per-monitor workspace slots
- Active dot filled with `@accent_color`
- Click group name → group switcher panel
- Scroll on dot row → workspace up/down (throttled)

---

### Center Zone — Live Status

Minimal by design. Items have a defined priority order for when horizontal
space is constrained: clock > notification badge > media controls > tray.

**Clock:** existing `MenuButton` with calendar popover. Always visible.

**Notification badge:** unread notification count. Hidden when zero. Clicking
opens notification history panel. *(Panel spec deferred — Phase 1.)*

**Media controls (minimal):** visible only when a player is active.

```
  [▶‖]  [⏭]  artist – title (truncated)
```

- Play/pause button (`media-playback-start/pause-symbolic`)
- Next button (`media-skip-forward-symbolic`)
- Track label truncated to available space, `@dim_label_color`
- No album art, no previous button, no progress — those live in the
  future center panel
- Bound to `AstalMpris` default player; if multiple players, shows
  the most recently active one
- Clicking the track label opens the full media panel *(deferred — Phase 1)*

**System tray:** small (20px) tray icons from `AstalTray`. Up to 3 always
visible; remainder behind `...` overflow button. Click opens native menu.
Configurable set of "always visible" app-ids via GSettings.

---

### Right Zone — System Status Pill

Single `Button` styled as a pill. Opens/closes DeviceMenu.

**Pill contents (left to right):**
- Microphone-in-use indicator (visible only when mic is active)
- Bluetooth icon (visible only when a device is connected)
- Network icon (always visible)
- Volume icon (always visible)
- Battery box: power profile icon + battery icon + percentage + time remaining
  (entire box hidden when no battery present)

**Warning/alert states on the pill:**
- Low battery (< 20%): battery icon uses `@warning_color`; subtle pill
  background tint
- Low peripheral battery (any device): small badge dot on pill
- No network: network icon changes to error variant
- Critical battery (< 5%): pill background uses `@error_bg_color` at low opacity

Pill does NOT flash, animate repeatedly, or show text alerts inline.

*Recording tile removed from initial scope — deferred to later.*

---

## OSD (On-Screen Display)

For transient feedback requiring no user interaction.

- **Position:** bottom-center, `$spacing` gap from screen edge
- **Shape:** pill (`$radius-pill`)
- **Background:** `@card_bg_color` semi-transparent, blur-ready
- **Auto-dismiss:** 1.5s after last triggering event
- **No interaction required**

```
        ╔════════════════════╗
        ║  🔊  ██████░░  72% ║
        ╚════════════════════╝
```

### OSD triggers

| Event | Display |
|-------|---------|
| Volume change | Speaker icon + level bar + percentage |
| Volume muted | Muted speaker icon + "Muted" |
| Brightness change | Brightness icon + level bar + percentage |
| Keyboard layout change | Keyboard icon + layout short name (e.g. "PL", "US") |

**Keyboard layout OSD notes:**
- Source: niri IPC (`niri msg keyboard-layouts` + event subscription) —
  preferred over GSettings polling
- Short name derived from XKB layout variant string
- Shares the same OSD widget and dismiss timer as volume/brightness
- Triggered by the `xkb options "grp:win_space_toggle"` keybind defined
  in `input.kdl`

---

## DeviceMenu (Quick Settings Panel)

### Window

- Width: `$panel-width` (456px), fixed
- Position: anchored top-right, below bar
- Background: `@card_bg_color` semi-transparent, blur-ready
- Corner radius: `$radius` (12px)
- No title bar

### Internal grid

6 columns, each 64px wide with 8px gutters. All sections span full width.

---

### Section 1 — Power Strip

Always visible. Sits at the top with a `$section-gap` margin below.

```
┌──────┬──────┬──────┬──────┬──────┬──────┐
│  🔒  │  💤  │  ↩  │  ⏻  │ ⏻x  │      │
│ Lock │Sleep │Logout│Reboot│ Off  │      │
└──────┴──────┴──────┴──────┴──────┴──────┘
```

- 5 icon-only buttons across 5 of 6 columns, `$tile-size` height
- Visually distinct from grid below: subtle separator or increased margin
- Destructive actions (logout, reboot, shutdown): Adwaita destructive styling
  on hover/focus only, not by default
- All are one-shot actions — no toggle state

---

### Section 2 — Toggle Grid

`Gtk.Grid` with 6 columns, `$tile-gap` spacing.

**Row 1 — always visible:**

| Col 1 | Col 2 | Col 3 | Col 4 | Col 5 | Col 6 |
|-------|-------|-------|-------|-------|-------|
| Dark mode | DND | Screenshot | _(spare)_ | _(spare)_ | _(spare)_ |

**Row 2 — laptop only** (hidden via `ShellProfileService.is_laptop`):

| Col 1 | Col 2 | Col 3 | Col 4 | Col 5 | Col 6 |
|-------|-------|-------|-------|-------|-------|
| Power saver | Balanced | Performance | Rotation lock | _(spare)_ | _(spare)_ |

*Recording tile deferred to later implementation.*

**Tile anatomy:**
- Size: `$tile-size` × `$tile-size` (64 × 64px)
- Corner radius: `$radius-tile` (10px)
- Inactive: `@card_bg_color` background
- Active/on: `@accent_bg_color` background, `@accent_fg_color` icon
- Icon only — no label text

**Special tile behaviors:**
- **Screenshot:** single tap calls `niri msg action screenshot`; not a toggle
- **Power profile tiles (laptop):** mutually exclusive; one active at a time
- **DND:** mirrors the DND state also accessible from notification history panel

---

### Section 3 — Panels

Ordered by frequency of use. Each panel is a `PanelRow` widget.

1. Audio (speaker)
2. Audio (microphone)
3. Brightness
4. Bluetooth
5. Devices
6. Network
7. Display *(Phase 2 — placeholder slot reserved)*
8. Home Assistant *(when configured)*
9. KDE Connect *(future — placeholder slot reserved)*

---

## PanelRow Widget

Reusable base structure for all DeviceMenu panels.

### Header row (always visible, 44px min height)

```
┌──────┬──────────────────────────┬──────┬──────┐
│ icon │  label / status / slider │ [on] │  ▾  │
│ 1col │         3–4 col          │ 1col │ 1col │
└──────┴──────────────────────────┴──────┴──────┘
```

- **Icon (1 col):** `Gtk.Button` styled `fixed-icon`; action depends on panel
  (mute toggle for audio, disabled/decorative for others)
- **Content (3–4 col, hexpand):** status label or `Gtk.Scale` slider
- **Toggle (1 col):** `Gtk.ToggleButton` on/off; hidden when panel has no
  binary state (Devices, Display)
- **Chevron (1 col):** `Gtk.Button` go-down/up; hidden when no revealer content

### Revealer (collapsible)

- Default: collapsed
- Contents: device list, AP list, light controls, etc.
- Item rows: `$radius-sm` corners, `$spacing-sm` gaps

### Caption row (optional)

Small `@dim_label_color` label below header. Visible only when revealer is
collapsed. Used for active device name.

---

## Panel Specifications

### Audio — Speaker

- **Icon:** mute toggle (`audio-volume-*-symbolic`)
- **Content:** volume slider (0–1.0, bidirectional)
- **Toggle:** hidden (mute is on the icon button)
- **Caption:** active speaker device name
- **Revealer:** available speaker device list

### Audio — Microphone

- Same structure as speaker, bound to default microphone
- **Icon:** mic mute toggle (`microphone-*-symbolic`)

### Brightness

- **Icon:** `display-brightness-symbolic` (non-interactive)
- **Content:** brightness slider (0–100)
- **Toggle:** hidden
- **Revealer:** per-monitor brightness sliders for multi-monitor setups

### Bluetooth

- **Icon:** `bluetooth-active-symbolic` or `bluetooth-disabled-symbolic`
- **Content:** status label ("Connected: MOMENTUM TW 4" or device count)
- **Toggle:** bluetooth on/off
- **Revealer header:** `FavoriteButton` shortcut rows
- **Revealer body:** full `BluetoothDevice` list
- **Note:** battery levels live in Devices panel, not here

### Devices

- **Icon:** `input-gaming-symbolic` or `devices-symbolic`
- **Content:** summary ("All OK" or "1 device low")
- **Toggle:** hidden
- **Chevron:** hidden when ≤ 3 devices (always expanded); visible otherwise
- **Body:**

```
  G502 X PLUS    🖱  ████████░░  82%
  MOMENTUM TW 4  🎧  ██████░░░░  61%
  ACCENTUM       🎧  ████░░░░░░  43%  ⚠
```

Battery bar states: good (> 40%), medium (20–40%), low (< 20% →
`@warning_color`), critical (< 5% → `@error_color`).
Low battery row gets subtle `@warning_color` left border or background tint.
Source: `ExternalBatteryService` via UPower D-Bus.

### Network

- **Icon:** current network type icon
- **Content:** SSID or connection name + signal strength
- **Toggle:** wifi on/off
- **Revealer:** AP list (Phase 1a: display only; Phase 1b: connect)

### Display *(Phase 2 placeholder)*

- **Icon:** `video-display-symbolic`
- **Content:** current output name + refresh rate
- **Toggle:** hidden
- **Revealer:** per-output resolution/refresh rate picker
- Only shown when `DisplayProfileService` is available

### Home Assistant *(when configured)*

- **Icon:** `home-symbolic`
- **Content:** "Connected" / "Offline"
- **Toggle:** hidden
- **Revealer:** light group rows, appliance notification rows

---

## Notification System

*(Full spec deferred. Structure decisions recorded.)*

### Bar integration

- Badge dot in center zone showing unread count
- Clicking badge opens notification history panel

### Popup (transient)

- Anchored top-right, below bar, per-monitor instances
- Auto-dismiss: normal 5s, critical persistent
- Action buttons when provided by notification

### History panel

- Scrollable list, newest first, grouped by app
- "Clear all" + DND toggle at top
- DND state shared with DeviceMenu DND tile

---

## Themes

### What themes control automatically

Any GTK theme implementing Adwaita color tokens correctly styles:
- All color states (active, inactive, warning, error)
- Text and icon colors
- Focus rings and hover states
- Libadwaita components when used

### What themes do NOT control

- Layout geometry (`$panel-width`, `$tile-size`, `$bar-height`)
- Border radii (SCSS variables)
- Blur (niri config)

### Theme-specific geometry overrides

`ui/themes/_lavanda.scss` and `ui/themes/_fluent.scss` pattern is correct.
Scope overrides to radius and spacing adjustments only — never colors.

### Blur activation (future)

When niri blur releases:

```kdl
// In rules.kdl — add when niri blur is available
window-rule {
    match app-id="py-desktop"
    // blur { passes 2; radius 20; }  ← uncomment when supported
}
```

In SCSS: reduce `$bar-bg-opacity` and `$panel-bg-opacity` to desired values,
or set backgrounds fully transparent and rely on blur entirely.

---

## Implementation Order

1. **SCSS token layer** — extract all geometry values into spec variables;
   replace all inline magic numbers throughout existing SCSS
2. **PanelRow base widget** — unified Python + Blueprint structure
3. **DeviceMenu layout** — power strip + toggle grid + panels using PanelRow
4. **OSD widget** — volume, brightness, keyboard layout triggers
5. **Individual new panels** — Devices, Network (Phase 1a), HA MVP
6. **Bar center zone** — media controls, notification badge, tray overflow
7. **Notification system** — full spec developed separately

---

## Open Questions

*(Record unresolved decisions here rather than guessing)*

- **Recording:** deferred. When revisited: `wf-recorder` subprocess vs future
  niri native screencast. Affects active state detection and stop mechanism.
- **Center zone panel:** no panel exists yet for the center zone. Content and
  interaction model to be designed when notification system is specced.
- **Tray overflow threshold:** suggest 3 always-visible + overflow button;
  needs real-world testing to tune.
- **KDE Connect:** placeholder slot in panel order. Implementation separate.
- **Group switcher UI:** bar left zone integration deferred to Phase 2
  workspace design.
