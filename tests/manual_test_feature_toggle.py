
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from ui.common.FeatureToggle import FeatureToggle

def test_feature_toggle_instantiation():
    try:
        toggle = FeatureToggle()
        print("FeatureToggle instantiated successfully")
        toggle.label = "Test Label"
        toggle.icon_name = "test-icon"
        print(f"Label: {toggle.label}, Icon: {toggle.icon_name}")
    except Exception as e:
        print(f"Failed to instantiate FeatureToggle: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_feature_toggle_instantiation()
