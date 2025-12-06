"""Bootstrap script for Secure Password Manager."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str]) -> None:
    """Run a subprocess and surface failures immediately."""
    subprocess.run(cmd, check=True)


def setup_project() -> None:
    """Create a virtualenv and install the editable package."""
    os.chdir(PROJECT_ROOT)
    venv_dir = PROJECT_ROOT / "venv"
    if not venv_dir.exists():
        print("Creating virtual environment...")
        _run([sys.executable, "-m", "venv", str(venv_dir)])

    if sys.platform.startswith("win"):
        python_bin = venv_dir / "Scripts" / "python.exe"
        activate_hint = "venv\\Scripts\\activate"
    else:
        python_bin = venv_dir / "bin" / "python"
        activate_hint = "source venv/bin/activate"

    print("Upgrading pip and installing project in editable mode...")
    _run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
    _run([str(python_bin), "-m", "pip", "install", "-e", "."])

    print("\nSetup complete! Next steps:")
    print(f"  1. Activate the venv: {activate_hint}")
    print("  2. Initialize the vault: password-manager --init")
    print("  3. Launch CLI or GUI: password-manager | password-manager-gui")


if __name__ == "__main__":
    setup_project()
