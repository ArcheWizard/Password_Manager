"""Setup script for Password Manager."""

import os
import subprocess
import sys


def setup_project():
    """Set up the project environment and dependencies."""
    print("Setting up Password Manager environment...")

    # Create virtual environment
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])

    # Determine activate script (Windows vs Unix)
    if sys.platform == "win32":
        activate_script = os.path.join("venv", "Scripts", "activate")
    else:
        activate_script = os.path.join("venv", "bin", "activate")

    # Install requirements
    print("Installing dependencies...")
    if sys.platform == "win32":
        subprocess.run("venv\\Scripts\\pip install -r requirements.txt", shell=True)
    else:
        subprocess.run("./venv/bin/pip install -r requirements.txt", shell=True)

    print("\nSetup complete! You can now run the Password Manager.")
    print("\nTo activate the virtual environment:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")

    print("\nTo run the application:")
    print("   python app.py")


if __name__ == "__main__":
    setup_project()
