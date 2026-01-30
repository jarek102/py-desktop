# Justfile

# --- Variables ---
src_dir := "src"
ui_dir := "ui"
data_dir := "data"
gen_dir := "generated"

# Target location for schemas
schema_target := env_var("HOME") / ".local/share/glib-2.0/schemas"

# Location for system gi-stubs repository
python_site := shell("python3 -c 'import site; print(site.getsitepackages()[0])'")
system_stubs := python_site / "gi-stubs"

# --- Main Commands ---

default: build run

# Build everything (checks for typings, compiles UI/Styles/Schemas)
build: prepare typings ui styles schema

# Run the application
run:
    python3 {{src_dir}}/main.py

# Watch mode (only watches UI/Styles, assumes typings are done)
watch:
    @echo "👀 Watching {{ui_dir}} for changes..."
    @find {{ui_dir}} -name "*.blp" -o -name "*.scss" | entr -s "just ui styles"

# Force regeneration of typings (if GObjects change or update Astal)
update-typings: clean-typings typings

clean:
    rm -rf {{gen_dir}}

clean-typings:
    rm -rf {{gen_dir}}/typings

# --- Build Steps ---

prepare:
    mkdir -p {{gen_dir}}/ui
    mkdir -p {{gen_dir}}/typings/gi

# 1. Typings (Smart Check)
# Only generates if Astal-4.0.pyi is missing.
typings:
    @if [ -f "{{gen_dir}}/typings/gi/repository/Astal-4.0.pyi" ]; then \
        echo "✅ Typings exist. Skipping generation (Run 'just update-typings' to force)."; \
    else \
        just _gen-typings; \
    fi

# Internal recipe: The actual generation + REPLACEMENT step
_gen-typings:
    @echo "⚙️  Generating GObject stubs (gengir)..."
    rm -rf {{gen_dir}}/typings/gi
    mkdir -p {{gen_dir}}/typings/gi

    gengir --out-dir {{gen_dir}}/typings/gi \
        Astal-4.0 AstalWp-0.1 AstalTray-0.1 AstalPowerProfiles-0.1 \
        AstalNotifd-0.1 AstalNiri-0.1 AstalNetwork-0.1 AstalMpris-0.1 \
        AstalIO-0.1 AstalHyprland-0.1 AstalGreet-0.1 AstalCava-0.1 \
        AstalBluetooth-0.1 AstalBattery-0.1 AstalAuth-0.1 AstalApps-0.1

    @echo "📥 Forcing system Gtk/Gio overrides..."
    @echo "   python_site = {{python_site}}"
    @echo "   system_stubs = {{system_stubs}}"

    @if [ -d {{system_stubs}} ]; then \
        echo "   📂 Found system stubs:"; \
        ls {{system_stubs}}; \
        rsync -a --delete {{system_stubs}}/ {{gen_dir}}/typings/gi/; \
        echo "   ✅ System stubs applied"; \
    else \
        echo "   ❌ gi-stubs directory missing"; \
    fi



# 2. Compile Blueprints
ui:
    @echo "🎨 Compiling Blueprints..."
    blueprint-compiler batch-compile {{gen_dir}}/ui {{ui_dir}} {{ui_dir}}/**/*.blp

# 3. Compile SCSS
styles:
    @echo "💄 Compiling Styles..."
    sass {{ui_dir}}/style.scss {{gen_dir}}/style.css

# 4. Install & Compile Schemas
schema:
    @echo "📋 Installing Schemas..."
    mkdir -p {{schema_target}}
    cp {{data_dir}}/*.gschema.xml {{schema_target}}/
    glib-compile-schemas {{schema_target}}

debug-stubs:
    @echo "🐍 python_site = {{python_site}}"
    @echo "📦 system_stubs = {{system_stubs}}"
    @ls -ld {{python_site}} || true
    @ls -ld {{system_stubs}} || true
    @ls -ld {{system_stubs}}/repository || true
