#!/usr/bin/env python3
import shutil
import subprocess
import pathlib
import sys

def compile_blueprints(root_dir):
    compiler = shutil.which("blueprint-compiler")
    if not compiler:
        print("Warning: 'blueprint-compiler' not found. Skipping blueprint compilation.")
        return

    blueprint_dir = root_dir / "ui"
    generated_dir = root_dir / "generated" / "ui"
    generated_dir.mkdir(parents=True, exist_ok=True)

    print("Compiling blueprints...")
    cmd = [
        compiler,
        "batch-compile",
        str(generated_dir),
        str(blueprint_dir),
    ]
    # Add all .blp files to the command
    cmd.extend([str(p) for p in blueprint_dir.rglob("*.blp")])

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(f"Error compiling blueprints")
        sys.exit(1)

def compile_stylesheets(root_dir):
    compiler = shutil.which("sass")
    if not compiler:
        print("Warning: 'sass' not found. Skipping stylesheet compilation.")
        return

    print("Compiling stylesheets...")
    scss_file = root_dir / "ui" / "style.scss"
    css_file = scss_file.with_suffix(".css")

    if not scss_file.exists():
        return

    if not css_file.exists() or scss_file.stat().st_mtime > css_file.stat().st_mtime:
        print(f"  {scss_file.name} -> {css_file.name}")
        try:
            subprocess.run([compiler, str(scss_file), str(css_file)], check=True)
        except subprocess.CalledProcessError:
            print(f"Error compiling {scss_file.name}")
            sys.exit(1)
    else:
        print(f"  {scss_file.name} (up to date)")

def main():
    # Determine paths relative to this script
    project_root = pathlib.Path(__file__).parent.resolve()
    
    # 1. Compile Blueprints
    compile_blueprints(project_root)
    compile_stylesheets(project_root)

    schema_filename = "com.github.jarek102.py-desktop.gschema.xml"
    schema_src = project_root / "data" / schema_filename
    
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

    try:
        if not shutil.which("glib-compile-schemas"):
             print("Error: 'glib-compile-schemas' not found.")
             sys.exit(1)
             
        subprocess.run(["glib-compile-schemas", str(schema_dir)], check=True)
        print("Success! Schema registered.")
    except subprocess.CalledProcessError:
        print("Error: Failed to compile schemas.")

if __name__ == "__main__":
    main()