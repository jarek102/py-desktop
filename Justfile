# --- Variables ---
src_dir := "src"
ui_dir := "ui"
data_dir := "data"
gen_dir := "generated"

# Target location for schemas
schema_target := env_var("HOME") / ".local/share/glib-2.0/schemas"

# Location for system gi-stubs
python_site := shell("python3 -c 'import site; print(site.getsitepackages()[0])'")
system_stubs := python_site / "gi-stubs"

# Location of girepository files
gir_dir := "/usr/lib/girepository-1.0"

# Derive Astal GIRs from versions.py (single source of truth)
# Produces: "Astal-4.0 AstalTray-0.1 ..." (space-separated)
astal_girs := shell("python3 - <<'PY'\nimport re\ngs = []\nwith open('src/versions.py') as f:\n    for line in f:\n        m = re.search(r\"require_version\\('([^']+)',\\s*'([^']+)'\\)\", line)\n        if m and m.group(1).startswith('Astal'):\n            gs.append(f\"{m.group(1)}-{m.group(2)}\")\nprint(' '.join(gs))\nPY")

# Stamp file used to detect typelib changes
typelib_stamp := gen_dir / "typings/.typelib.stamp"

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
    @find {{ui_dir}} -name "*.blp" -o -name "*.scss" | entr -r sh -c 'just ui styles'

update-typings:
    rm -f {{typelib_stamp}}
    just typings

clean:
    rm -rf {{gen_dir}}

clean-typings:
    rm -rf {{gen_dir}}/typings

# --- Build Steps ---

prepare:
    mkdir -p {{gen_dir}}/ui
    mkdir -p {{gen_dir}}/typings/gi

# Update the stamp by hashing mtimes of matching Astal typelibs
update-typelib-stamp:
    @mkdir -p {{gen_dir}}/typings
    @stat -c '%y' {{gir_dir}}/Astal*.typelib \
        | sha256sum | cut -d' ' -f1 > {{typelib_stamp}}.new

# Decide whether to run gengir (only when Astal typelibs changed)
maybe-gen-astal: prepare update-typelib-stamp
    @if [ -f {{typelib_stamp}} ] && cmp -s {{typelib_stamp}} {{typelib_stamp}}.new; then \
        echo "✅ Astal typelibs unchanged — skipping gengir"; \
        rm {{typelib_stamp}}.new; \
    else \
        echo "♻️  Astal typelibs changed — running gengir"; \
        just _gen-typings; \
        mv {{typelib_stamp}}.new {{typelib_stamp}}; \
    fi

# Public target
typings: maybe-gen-astal

# Internal recipe: run gengir (on GIRs discovered from versions.py) and overlay system stubs
_gen-typings:
    @echo "⚙️  Generating GObject stubs (gengir)..."
    rm -rf {{gen_dir}}/typings/gi
    mkdir -p {{gen_dir}}/typings/gi

    gengir --out-dir {{gen_dir}}/typings/gi {{astal_girs}}

    @echo "📥 Overlaying system Gtk/Gio stubs..."
    @echo "   system_stubs = {{system_stubs}}"

    @if [ -d {{system_stubs}} ]; then \
        rsync -a --delete {{system_stubs}}/ {{gen_dir}}/typings/gi/; \
        echo "   ✅ System stubs applied"; \
    else \
        echo "   ❌ gi-stubs missing — typing will be degraded"; \
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

# Verify overlay result (useful for CI)
verify-stubs:
    @grep -q "typing.Protocol" {{gen_dir}}/typings/gi/repository/Gtk-4.0.pyi \
        && echo "✅ Gtk stubs look sane" \
        || (echo "❌ Gtk stubs look wrong" && exit 1)
