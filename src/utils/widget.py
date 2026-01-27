import pathlib
from gi.repository import Gtk

# Path to the 'src' directory (parent of utils)
SRC_ROOT = pathlib.Path(__file__).parent.parent
GENERATED_DIR = SRC_ROOT / "generated"

def Blueprint(ui_file: str = None):
    def decorator(cls):
        nonlocal ui_file
        if ui_file is None:
            ui_file = f"{cls.__name__}.ui"
        
        if ui_file.endswith(".blp"):
            ui_file = ui_file.replace(".blp", ".ui")
            
        template_path = GENERATED_DIR / ui_file
        return Gtk.Template(filename=str(template_path))(cls)
    return decorator