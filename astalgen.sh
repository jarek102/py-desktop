#!/bin/bash
set -e

# 1. Define Paths
# Automatically find where 'paru' installed the good stubs
# On Arch, this is usually /usr/lib/python3.X/site-packages/gi-stubs
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
SYSTEM_STUBS="$SITE_PACKAGES/gi-stubs"

if [ ! -d "$SYSTEM_STUBS" ]; then
    echo "⚠️  WARNING: Could not find system stubs at $SYSTEM_STUBS"
    echo "   Make sure 'python-pygobject-stubs' is installed via paru."
    exit 1
fi

echo "🧹 Cleaning old local stubs..."
rm -rf generated/typings
mkdir -p generated/typings/gi

# 2. Generate Astal stubs (Low Quality, but necessary)
echo "⚙️  Generating Astal stubs (using gengir)..."
# Note: We generate these into ./generated/typings/gi so they land in typings/gi/repository/
for lib in \
    "Astal-4.0" \
    "AstalWp-0.1" \
    "AstalTray-0.1" \
    "AstalPowerProfiles-0.1" \
    "AstalNotifd-0.1" \
    "AstalNiri-0.1" \
    "AstalNetwork-0.1" \
    "AstalMpris-0.1" \
    "AstalIO-0.1" \
    "AstalHyprland-0.1" \
    "AstalGreet-0.1" \
    "AstalCava-0.1" \
    "AstalBluetooth-0.1" \
    "AstalBattery-0.1" \
    "AstalAuth-0.1" \
    "AstalApps-0.1"
do
    echo "  -> Processing $lib..."
    gengir "$lib" -o ./generated/typings/gi > /dev/null
done

# 3. CRITICAL: Merge System Stubs (High Quality)
# We copy the system stubs *on top* of the generated ones.
# This replaces the unannotated 'gengir' version of Gtk/Gio with the high-quality one.
echo "📥 Pulling high-quality system stubs from $SYSTEM_STUBS..."
cp -rf "$SYSTEM_STUBS/"* ./generated/typings/gi/

echo "✅ Done! Monolithic stub library created in ./generated/typings"
echo "   - Astal: From gengir"
echo "   - Gtk/Gio: From system packages"
