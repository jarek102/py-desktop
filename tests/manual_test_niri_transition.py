
import sys
import time
import gi

try:
    gi.require_version('AstalNiri', '0.1')
    from gi.repository import AstalNiri, GLib
except ValueError:
    print("AstalNiri 0.1 not found.")
    sys.exit(1)
except ImportError:
    print("Cannot import AstalNiri.")
    sys.exit(1)

def test_transition(delay):
    print(f"Testing do_screen_transition with delay={delay}...")
    try:
        # Verify if method exists
        if not hasattr(AstalNiri.msg, 'do_screen_transition'):
            print("Error: AstalNiri.msg does not have do_screen_transition method.")
            return

        try:
             # Create Variant 'x' for int64.
             v_delay = GLib.Variant('x', delay) 
             result = AstalNiri.msg.do_screen_transition(v_delay)
        except TypeError as e:
             print(f"TypeError with Variant: {e}, trying raw int...")
             result = AstalNiri.msg.do_screen_transition(delay)
             
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception during call: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 manual_test_niri_transition.py <delay>")
        sys.exit(1)
        
    delay = int(sys.argv[1])
    test_transition(delay)
