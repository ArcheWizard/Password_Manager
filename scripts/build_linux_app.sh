#!/bin/bash

# Linux Application Builder for Secure Password Manager
# This script creates a standalone Linux executable bundle

set -e  # Exit on error

echo "========================================"
echo "  Password Manager Linux App Builder"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the script directory and move to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Read version
VERSION=$(cat VERSION.txt | tr -d '\n')
echo -e "${GREEN}Building version: $VERSION${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade necessary packages
echo "Installing build dependencies..."
pip install --upgrade pip
pip install pyinstaller
pip install -r requirements.txt

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/
rm -rf dist/password-manager
rm -rf dist/password-manager-gui
rm -rf dist/password-manager-linux/

# Create spec files for better control
echo ""
echo "Creating PyInstaller spec files..."

# CLI spec file
cat > password-manager.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['apps/app.py'],
    pathex=[],
    binaries=[],
    datas=[('VERSION.txt', '.'), ('README.md', '.')],
    hiddenimports=['cryptography', 'colorama', 'pyperclip', 'pyotp', 'qrcode', 'requests'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='password-manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

# GUI spec file
cat > password-manager-gui.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['apps/gui.py'],
    pathex=[],
    binaries=[],
    datas=[('VERSION.txt', '.'), ('README.md', '.')],
    hiddenimports=['cryptography', 'PyQt5', 'pyperclip', 'pyotp', 'qrcode', 'requests', 'zxcvbn'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='password-manager-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

echo -e "${GREEN}✓ Spec files created${NC}"
echo ""

# Build CLI version
echo "Building CLI version..."
pyinstaller --clean password-manager.spec
echo -e "${GREEN}✓ CLI build complete${NC}"
echo ""

# Build GUI version
echo "Building GUI version..."
pyinstaller --clean password-manager-gui.spec
echo -e "${GREEN}✓ GUI build complete${NC}"
echo ""

# Create application directory structure
echo "Creating application bundle..."
APP_DIR="dist/password-manager-linux"
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/bin"
mkdir -p "$APP_DIR/docs"
mkdir -p "$APP_DIR/share"

# Move executables
mv dist/password-manager "$APP_DIR/bin/"
mv dist/password-manager-gui "$APP_DIR/bin/"

# Copy documentation
cp README.md "$APP_DIR/"
cp CHANGELOG.md "$APP_DIR/"
cp VERSION.txt "$APP_DIR/"
cp -r docs/* "$APP_DIR/docs/" 2>/dev/null || true

echo -e "${GREEN}✓ Application bundle created${NC}"
echo ""

# Create launcher scripts
echo "Creating launcher scripts..."

cat > "$APP_DIR/password-manager" << 'EOF'
#!/bin/bash
# Launcher script for Password Manager CLI

# Get the directory where this script is located
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the application
exec "$DIR/bin/password-manager" "$@"
EOF
chmod +x "$APP_DIR/password-manager"

cat > "$APP_DIR/password-manager-gui" << 'EOF'
#!/bin/bash
# Launcher script for Password Manager GUI

# Get the directory where this script is located
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure XDG directories exist
mkdir -p "$HOME/.local/share/password-manager"
mkdir -p "$HOME/.config/password-manager"

# Run the application
exec "$DIR/bin/password-manager-gui" "$@"
EOF
chmod +x "$APP_DIR/password-manager-gui"

echo -e "${GREEN}✓ Launcher scripts created${NC}"
echo ""

# Create desktop entry
echo "Creating desktop entry..."
cat > "$APP_DIR/password-manager.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Secure Password Manager
Comment=Manage your passwords securely with encryption
Exec=/opt/password-manager/password-manager-gui
Icon=password-manager
Terminal=false
Categories=Utility;Security;
Keywords=password;security;encryption;
StartupNotify=true
EOF

echo -e "${GREEN}✓ Desktop entry created${NC}"
echo ""

# Create installation script
echo "Creating installation script..."
cat > "$APP_DIR/install.sh" << 'INSTALL_EOF'
#!/bin/bash

# Installation script for Password Manager

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================"
echo "  Password Manager Installation"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run with sudo: sudo ./install.sh${NC}"
    exit 1
fi

# Create installation directory
INSTALL_DIR="/opt/password-manager"
echo -e "${YELLOW}Installing to $INSTALL_DIR...${NC}"
mkdir -p "$INSTALL_DIR"

# Copy files
echo "Copying application files..."
cp -r bin/ "$INSTALL_DIR/"
cp -r docs/ "$INSTALL_DIR/"
cp README.md CHANGELOG.md VERSION.txt "$INSTALL_DIR/"
cp password-manager "$INSTALL_DIR/"
cp password-manager-gui "$INSTALL_DIR/"
cp password-manager.desktop "$INSTALL_DIR/"

# Create symlinks
echo "Creating symbolic links..."
ln -sf "$INSTALL_DIR/password-manager" /usr/local/bin/password-manager
ln -sf "$INSTALL_DIR/password-manager-gui" /usr/local/bin/password-manager-gui

# Install desktop entry
echo "Installing desktop entry..."
mkdir -p /usr/share/applications
cp "$INSTALL_DIR/password-manager.desktop" /usr/share/applications/
sed -i "s|Exec=.*|Exec=$INSTALL_DIR/password-manager-gui|g" /usr/share/applications/password-manager.desktop

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications/
fi

# Set permissions
chmod +x "$INSTALL_DIR/password-manager"
chmod +x "$INSTALL_DIR/password-manager-gui"
chmod +x "$INSTALL_DIR/bin/password-manager"
chmod +x "$INSTALL_DIR/bin/password-manager-gui"

echo ""
echo -e "${GREEN}========================================"
echo "  Installation Complete!"
echo "========================================${NC}"
echo ""
echo "You can now run:"
echo "  • CLI: password-manager"
echo "  • GUI: password-manager-gui"
echo ""
echo "Or search for 'Secure Password Manager' in your application menu."
echo ""
INSTALL_EOF
chmod +x "$APP_DIR/install.sh"

echo -e "${GREEN}✓ Installation script created${NC}"
echo ""

# Create uninstall script
echo "Creating uninstall script..."
cat > "$APP_DIR/uninstall.sh" << 'UNINSTALL_EOF'
#!/bin/bash

# Uninstallation script for Password Manager

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================"
echo "  Password Manager Uninstallation"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run with sudo: sudo ./uninstall.sh${NC}"
    exit 1
fi

# Warning
echo -e "${YELLOW}This will remove Password Manager from your system.${NC}"
echo -e "${YELLOW}Your password data will NOT be deleted.${NC}"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Remove symlinks
echo "Removing symbolic links..."
rm -f /usr/local/bin/password-manager
rm -f /usr/local/bin/password-manager-gui

# Remove installation directory
echo "Removing installation directory..."
rm -rf /opt/password-manager

# Remove desktop entry
echo "Removing desktop entry..."
rm -f /usr/share/applications/password-manager.desktop

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications/
fi

echo ""
echo -e "${GREEN}Uninstallation complete!${NC}"
echo ""
echo "Your password data remains in your home directory."
echo ""
UNINSTALL_EOF
chmod +x "$APP_DIR/uninstall.sh"

echo -e "${GREEN}✓ Uninstall script created${NC}"
echo ""

# Create README for the package
echo "Creating package README..."
cat > "$APP_DIR/INSTALL_README.txt" << 'README_EOF'
Secure Password Manager - Linux Application Package
====================================================

This package contains a standalone version of Secure Password Manager
that can be installed on any Linux system.

INSTALLATION
------------

Method 1: System-wide installation (Recommended)
   sudo ./install.sh

   This will install the application to /opt/password-manager and make
   it available system-wide.

Method 2: Run from this directory
   ./password-manager        # CLI version
   ./password-manager-gui    # GUI version

UNINSTALLATION
--------------

If you installed system-wide:
   cd /opt/password-manager
   sudo ./uninstall.sh

DATA LOCATION
-------------

Your password data is stored in:
   - Database: Current working directory (passwords.db)
   - Encryption keys: Current working directory
   - Logs: ./logs/

For system-wide installation, it's recommended to run the application
from your home directory so your data stays private.

REQUIREMENTS
------------

- Linux (x86_64)
- No Python installation required (bundled)
- For GUI: X11 or Wayland display server

TROUBLESHOOTING
---------------

If you encounter "cannot execute binary file":
   chmod +x password-manager password-manager-gui

If GUI doesn't start:
   - Ensure you have a display server running
   - Install missing libraries: sudo apt install libxcb-xinerama0

For more help, see the documentation in the docs/ directory
or visit: https://github.com/ArcheWizard/password-manager

README_EOF

echo -e "${GREEN}✓ Package README created${NC}"
echo ""

# Create tarball
echo "Creating distributable archive..."
cd dist
ARCHIVE_NAME="password-manager-${VERSION}-linux-x86_64.tar.gz"
tar -czf "$ARCHIVE_NAME" password-manager-linux/
cd ..

echo -e "${GREEN}✓ Archive created: dist/$ARCHIVE_NAME${NC}"
echo ""

# Display summary
echo ""
echo -e "${GREEN}========================================"
echo "  Build Complete!"
echo "========================================${NC}"
echo ""
echo "Output files:"
echo "  • Application bundle: dist/password-manager-linux/"
echo "  • Archive: dist/$ARCHIVE_NAME"
echo ""
echo "To test locally:"
echo "  cd dist/password-manager-linux"
echo "  ./password-manager-gui"
echo ""
echo "To install system-wide:"
echo "  cd dist/password-manager-linux"
echo "  sudo ./install.sh"
echo ""
echo "To distribute:"
echo "  Share the file: dist/$ARCHIVE_NAME"
echo ""
echo "Users can extract and run:"
echo "  tar -xzf $ARCHIVE_NAME"
echo "  cd password-manager-linux"
echo "  sudo ./install.sh"
echo ""
