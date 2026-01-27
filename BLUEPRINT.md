# Blueprint Guide

This project uses **Blueprint** (`.blp`) to define user interfaces. 

GTK Blueprint is a declarative UI language that compiles to GtkBuilder XML (`.ui`).

It provides:

* Cleaner syntax than XML
* Strong typing and validation
* Expressions and bindings
* Templates for custom widgets
* Menu definitions
* Extensibility

## 1. Workflow

1.  **Create** a `.blp` file in `src/ui/` (e.g., `src/ui/MyWidget.blp`).
2.  **Compile** it by running `python install.py`. This generates a `.ui` file in `src/generated/`.
3.  **Load** it in Python using the `@Blueprint` decorator.

## 2. Python Integration

We use a custom decorator to handle the path resolution for generated files.

```python
from gi.repository import Gtk, Astal, GObject
from utils import Blueprint

@Blueprint("MyWidget.blp")
class MyWidget(Astal.Box):
    __gtype_name__ = "MyWidget"
    
    # Binding targets must be GObject Properties
    label_text = GObject.Property(type=str, default="Hello")

    def __init__(self):
        super().__init__()
```

## 2. Template Architecture

Every UI component should be defined as a `template` to allow direct interaction with its Python class.

### Blueprint Definition (`MyWidget.blp`)

```blueprint
using Gtk 4.0;
using Adw 1;
using Astal 4.0;

template $MyWidget : Box {
  // 1. Properties
  hexpand: true;
  spacing: 12;
  styles ["my-custom-class"]

  // 2. Child widgets
  Label title {
    label: _("My Widget"); // _() marks for translation
    styles ["title-4"];
  }
}

```

### Python Registration (`MyWidget.py`)

```python
@Blueprint("MyWidget.ui")
class MyWidget(Gtk.Box):
    __gtemplate_name__ = "MyWidget"
    
    # Widget IDs in .blp automatically become accessible via self.title
    title = Gtk.Template.Child() 

```

---

## 3. Reactive Data Binding

Blueprint allows you to bind widget properties directly to GObject properties defined in your Python classes.

| Pattern | Blueprint Syntax | Use Case |
| --- | --- | --- |
| **Property Bind** | `label: bind template.text_prop;` | Syncing a label with a Python string. |
| **Two-way Bind** | `active: bind template.is_enabled bidirectional;` | Syncing a `Switch` or `Entry` with state. |
| **Inversion** | `visible: bind !template.is_hidden;` | Hiding widgets based on boolean flags. |
| **Expressions** | `label: bind template.val > 50 ? "High" : "Low";` | Inline conditional logic. |

---

## 4. Signal Handling

Connect signals (like clicks or changes) to Python methods using the `=>` operator. Prepend `$` to the method name to reference the template instance.

```blueprint
Button {
  clicked => $on_button_clicked();
}

Scale {
  value-changed => $on_slider_moved();
}

```

---

## 5. Desktop Component Examples

### A. The Status Bar (Astal Window)

In your project, the `Bar` is an `Astal.Window` that anchors to the screen edges.

```blueprint
using Gtk 4.0;
using Astal 4.0;

template $Bar : Astal.Window {
  anchor: top left right;
  exclusivity: exclusive;
  layer: top;

  CenterBox {
    start-widget: Box { /* Left Modules */ };
    center-widget: Label { label: bind template.time; };
    end-widget: Box { /* Right Modules */ };
  }
}

```

### B. Quick Settings Tile (Bluetooth/Network)

Follow the "Workbench style": use a `Box` inside a `Button` with a `title` and `subtitle`.

```blueprint
template $BluetoothDevice : Box {
  hexpand: true;
  styles ["item"]

  Image {
    icon-name: bind template.icon; // Bound to Python prop
  }

  Box {
    orientation: vertical;
    valign: center;

    Label {
      label: bind template.name;
      halign: start;
      styles ["title"];
    }

    Label {
      label: bind template.status;
      halign: start;
      styles ["subtitle"];
      visible: bind template.status != "";
    }
  }
}

```

### C. Volume/Brightness Slider

Combine an icon and a `Scale` for a professional system slider.

```blueprint
Box {
  spacing: 8;
  
  Image {
    icon-name: "audio-volume-high-symbolic";
  }

  Scale {
    hexpand: true;
    draw-value: false;
    adjustment: Adjustment {
      lower: 0;
      upper: 100;
      step-increment: 2;
    };
    value: bind template.volume;
  }
}

```

---

## 6. Best Practices

* **Adw Styles:** Use Libadwaita CSS classes like `.title-4`, `.subtitle`, `.card`, and `.boxed-list` for a native GNOME look.
* **Spacing:** Prefer `spacing: 12;` for main layouts and `spacing: 6;` for compact groups.
* **No Logic in UI:** Keep all math and string formatting in Python; use Blueprint only for structure and direct property binds.

# Examples

## 2. Minimal Example

```blp
using Gtk 4.0;

Gtk.Window {
    title: "Hello Blueprint";
    default-width: 400;
    default-height: 200;

    Gtk.Box {
        orientation: vertical;
        spacing: 12;
        margin-top: 12;
        margin-bottom: 12;
        margin-start: 12;
        margin-end: 12;

        Gtk.Label {
            label: "Hello, world!";
        }

        Gtk.Button {
            label: "Click me";
        }
    }
}
```

Key points:

* `using Gtk 4.0;` imports the namespace
* Objects are written as `TypeName { ... }`
* Properties use `property-name: value;`
* Children are nested

---

## 3. Document Root

A file can contain:

* `using` statements
* Object definitions
* Templates
* Menus

Example structure:

```blp
using Gtk 4.0;
using Adw 1;

Gtk.ApplicationWindow { ... }

menu main_menu { ... }

template MyWidget : Gtk.Box { ... }
```

---

## 4. Objects and Properties

### Basic syntax

```blp
Gtk.Button {
    label: "Save";
    sensitive: true;
}
```

### Nested children

```blp
Gtk.Box {
    Gtk.Label { label: "Name"; }
    Gtk.Entry {}
}
```

### Setting object IDs

```blp
Gtk.Button my_button {
    label: "OK";
}
```

This allows referencing the object elsewhere.

---

## 5. Values

Supported value types include:

* Strings: `"text"`
* Integers / floats: `12`, `3.14`
* Booleans: `true`, `false`
* Enums: `horizontal`, `center`, etc.
* Flags: `expand | fill`
* Objects
* Lists

Examples:

```blp
orientation: vertical;
hexpand: true;
margins: [12, 12, 12, 12];
```

---

## 6. Expressions and Bindings

Blueprint supports expressions using `bind` and `expr`.

### Property binding

```blp
Gtk.Label {
    label: bind my_entry.text;
}
```

### With transformation

```blp
Gtk.Label {
    label: expr my_entry.text + "!";
}
```

### Boolean logic

```blp
sensitive: expr my_entry.text != "";
```

---

## 7. Templates (Custom Widgets)

Templates allow defining reusable widgets tied to a GObject class.

```blp
template MyWidget : Gtk.Box {
    spacing: 6;

    Gtk.Label title_label {
        label: "Title";
    }

    Gtk.Button {
        label: "Action";
    }
}
```

Usage:

```blp
MyWidget {
}
```

In code (C / Rust / Python), you bind this template to your widget class.

---

## 8. Menus

Blueprint can define `GMenuModel` structures.

```blp
menu app_menu {
    section {
        item {
            label: "About";
            action: "app.about";
        }

        item {
            label: "Quit";
            action: "app.quit";
        }
    }
}
```

Attach to a window or application via code or properties.

---

## 9. Using libadwaita (Adw)

```blp
using Gtk 4.0;
using Adw 1;

Adw.ApplicationWindow {
    title: "Adwaita App";

    Adw.HeaderBar {
        title-widget: Gtk.Label { label: "Demo"; };
    }
}
```

---

## 10. Example from Workbench‑style UI

Simplified boxed list example:

```blp
using Gtk 4.0;
using Adw 1;

Adw.PreferencesPage {
    Adw.PreferencesGroup {
        title: "Settings";

        Adw.ActionRow {
            title: "Enable feature";

            Gtk.Switch {
                valign: center;
            }
        }

        Adw.ActionRow {
            title: "Username";

            Gtk.Entry {
                hexpand: true;
            }
        }
    }
}
```

This pattern is very common in Workbench demos and modern GNOME apps.

---

## 11. Diagnostics

The compiler reports:

* Syntax errors
* Invalid properties
* Type mismatches
* Unknown objects

Example:

```
error: Unknown property “labell” on Gtk.Button
```

Use it to catch UI mistakes early.

---

## Blueprint file: `custom_widget.blp`

```blp
using Gtk 4.0;

// Define a reusable widget template

template $CustomWidget : Gtk.Box {
    orientation: horizontal;
    spacing: 8;

    Gtk.Label title_label {
        label: "Hello";
    }

    Gtk.Button action_button {
        label: "Click";
    }
}
```

Important syntax:

* `template $CustomWidget : Gtk.Box` → defines a new widget type
* `$CustomWidget` → class name used in code
* `title_label` / `action_button` → child IDs used for binding

---

## Python file: `custom_widget.py`

```python
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

@Gtk.Template(filename="custom_widget.ui")
class CustomWidget(Gtk.Box):
    __gtype_name__ = "CustomWidget"

    title_label = Gtk.Template.Child()
    action_button = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self.action_button.connect("clicked", self.on_clicked)

    def on_clicked(self, button):
        self.title_label.set_text("Clicked!")
```

---

## Using the widget

```python
win = Gtk.Window()
win.set_child(CustomWidget())
win.present()
```

---

## Step 1 – Child widget template: `device_item.blp`

```blp
using Gtk 4.0;

template $DeviceItem : Gtk.Box {
    orientation: horizontal;
    spacing: 6;

    Gtk.Label name_label {
        label: "Device";
        hexpand: true;
    }

    Gtk.Button connect_button {
        label: "Connect";
    }
}
```

---

## Python: `device_item.py`

```python
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

@Gtk.Template(filename="device_item.ui")
class DeviceItem(Gtk.Box):
    __gtype_name__ = "DeviceItem"

    name_label = Gtk.Template.Child()
    connect_button = Gtk.Template.Child()

    def __init__(self, name):
        super().__init__()
        self.name_label.set_text(name)
```

---

## Step 2 – Container widget template: `bluetooth_menu.blp`

```blp
using Gtk 4.0;

// Container widget holding many DeviceItem widgets

template $BluetoothMenu : Gtk.Box {
    orientation: vertical;
    spacing: 8;
}
```

---

## Python: `bluetooth_menu.py`

```python
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from device_item import DeviceItem

@Gtk.Template(filename="bluetooth_menu.ui")
class BluetoothMenu(Gtk.Box):
    __gtype_name__ = "BluetoothMenu"

    def __init__(self):
        super().__init__()

        for name in ["Keyboard", "Mouse", "Headphones"]:
            self.append(DeviceItem(name))
```

---

## 29. Python Example 5 – Services and Shared Application State

This example is inspired by your `BrightnessService` and `WindowManager` classes.

It demonstrates how to structure non‑UI logic as **services** and connect them to Blueprint widgets using properties and bindings.

---

## Goal

We want:

* A central object that stores state (brightness)
* Multiple widgets that react to it
* No tight coupling between widgets

---

## Architecture

```
BrightnessService (GObject)
        ▲
        │ (property binding)
        ▼
BrightnessWidget (template widget)
```

---

## Service: `brightness_service.py`

```python
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import GObject

class BrightnessService(GObject.GObject):
    brightness = GObject.Property(type=int, default=50)

    def increase(self):
        self.brightness = min(100, self.brightness + 10)

    def decrease(self):
        self.brightness = max(0, self.brightness - 10)
```

---

## Widget template: `brightness_widget.blp`

```blp
using Gtk 4.0;

template $BrightnessWidget : Gtk.Box {
    orientation: horizontal;
    spacing: 8;

    Gtk.Button minus_btn {
        label: "-";
    }

    Gtk.Label value_label {
        label: bind service.brightness;
    }

    Gtk.Button plus_btn {
        label: "+";
    }
}
```

---

## Widget code: `brightness_widget.py`

```python
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

@Gtk.Template(filename="brightness_widget.ui")
class BrightnessWidget(Gtk.Box):
    __gtype_name__ = "BrightnessWidget"

    minus_btn = Gtk.Template.Child()
    plus_btn = Gtk.Template.Child()

    def __init__(self, service):
        super().__init__()
        self.service = service

        self.minus_btn.connect("clicked", lambda *_: service.decrease())
        self.plus_btn.connect("clicked", lambda *_: service.increase())
```

---

## Binding the service

In Python, expose the service to Blueprint:

```python
widget.service = brightness_service
```

Full example usage:

```python
service = BrightnessService()
widget = BrightnessWidget(service)
widget.service = service
```
---

## 33. Why LLMs Struggle With GTK Blueprint (Real‑World Pitfalls)

This section is based on real conversations and error logs while integrating Blueprint into the Ignis project.

It documents **systematic failure modes** of LLMs when working with Blueprint and how to correct them.

---

## Root causes

Blueprint is difficult for LLMs because:

* It is niche and under‑represented in training data
* It looks similar to GtkBuilder XML but is a different language
* It overlaps conceptually with Python `Gtk.Template`
* Its grammar is strict (semicolons, single template per file, etc.)
* GTK widget APIs differ subtly between classes (Button vs ToggleButton, etc.)

---

## Common hallucinations and their fixes

### 1. Using `id:` properties (XML habit)

❌ Hallucinated:

```blp
Gtk.Button {
    id: toggle_button;
}
```

✅ Correct Blueprint:

```blp
Gtk.Button toggle_button {
}
```

Rule: **object names define child IDs**, not properties.

---

### 2. Declaring children as `$var: Type`

❌ Hallucinated:

```blp
$toggle_button: Button;
```

✅ Correct:

```blp
Gtk.Button toggle_button { }
```

Blueprint does not support variable declarations.

---

### 3. Multiple templates in one file

❌ Hallucinated:

```blp
template $Group : Gtk.Box { }
template $Item : Gtk.ListBoxRow { }
```

✅ Correct:

One template per file:

```
bluetooth-group.blp
bluetooth-item.blp
```

---

### 4. Python-only features used in Blueprint

❌ Hallucinated:

```blp
gtk-template-child: toggle_button;
```

✅ Correct:

Use object names + `gtk_template_child()` in Python.

---

### 5. Wrong comment syntax

❌ Hallucinated:

```blp
# comment
```

✅ Correct:

```blp
// comment
/* multiline */
```

---

### 6. Missing semicolons

❌ Hallucinated:

```blp
icon-name: "bluetooth-symbolic"
```

✅ Correct:

```blp
icon-name: "bluetooth-symbolic";
```

---

### 7. Non‑existent properties (`styles`, `spacing` on ListBox, etc.)

❌ Hallucinated:

```blp
styles: ["rounded"];
```

Problems:

* Requires Blueprint extensions
* Not supported on many widgets

✅ Safer pattern:

```blp
styles [ "rounded" ]
```

or apply CSS in Python.

---

### 8. Widget API guessing

❌ Hallucinated:

```python
button.set_active(True)
```

✅ Correct:

```python
Gtk.ToggleButton.set_active(...)
```

Rule: Only ToggleButton supports `set_active()`.

---

### 9. Confusing GtkBuilder XML with Blueprint

Common invalid hybrids:

* `<object>` tags
* `property` blocks
* XML‑style IDs

Blueprint is its own language.

---

### 10. Property typing confusion (GI + type checkers)

LLMs often try to "fix":

```python
service.powered = True
```

because type checkers complain.

But this is valid for GObject properties.

Optional safe form:

```python
service.set_property("powered", True)
```

---

## Typical compiler errors and their meaning

| Error | Meaning |
|------|--------|
| `Expected ;` | Missing semicolon |
| `property called id` | XML syntax used |
| `Only one template per file` | File structure invalid |
| `Unexpected tokens` | Grammar violation |
| `Invalid property` | Widget does not support property |

---

## Recommended workflow when using LLMs with Blueprint

1. Generate **small snippets only**
2. Immediately run `blueprint-compiler`
3. Fix grammar before logic
4. Validate widget APIs via GTK docs