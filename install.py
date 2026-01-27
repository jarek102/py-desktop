#!/usr/bin/env python3
import shutil
import subprocess
import pathlib
import sys

def main():
    # Determine paths relative to this script
    project_root = pathlib.Path(__file__).parent.resolve()
    schema_filename = "com.github.jarek102.py-desktop.gschema.xml"
    schema_src = project_root / "src" / schema_filename
    
    # Standard user-local schema directory
    schema_dir = pathlib.Path.home() / ".local" / "share" / "glib-2.0" / "schemas"
    
    if not schema_src.exists():
        print(f"Error: Source schema not found at {schema_src}")
        sys.exit(1)
        
    print(f"Installing schema to {schema_dir}...")
    
    # Ensure destination directory exists
    schema_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy the schema file
    shutil.copy(schema_src, schema_dir)
    
    # Compile schemas
    print("Compiling schemas...")

    if not shutil.which("glib-compile-schemas"):
        print("Error: 'glib-compile-schemas' executable not found in PATH.")
        sys.exit(1)

    try:
        subprocess.run(["glib-compile-schemas", str(schema_dir)], check=True)
        print("Success! Schema registered.")
    except subprocess.CalledProcessError:
        print("Error: Failed to compile schemas.")

if __name__ == "__main__":
    main()