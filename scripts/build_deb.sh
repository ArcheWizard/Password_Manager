#!/bin/bash

# Debian Package Builder for Secure Password Manager
# Creates a .deb package for Debian/Ubuntu systems

set -e

echo "========================================"
echo "  Password Manager .deb Builder"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory and move to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Read version
VERSION=$(cat VERSION.txt | tr -d '\n' | sed 's/^v//')
PACKAGE_VERSION="${VERSION}"
PACKAGE_NAME="password-manager"
ARCH="amd64"

echo -e "${GREEN}Building .deb package for version: $VERSION${NC}"
echo ""

# Check for required tools
if ! command -v dpkg-deb &> /dev/null; then
    echo -e "${RED}Error: dpkg-deb not found. Please install: sudo apt install dpkg${NC}"
    exit 1
fi

# Create package directory structure
DEB_DIR="${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}"
echo "Creating package structure..."
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/opt/password-manager/bin"
mkdir -p "$DEB_DIR/opt/password-manager/docs"
mkdir -p "$DEB_DIR/usr/local/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/doc/password-manager"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing build dependencies..."
pip install --upgrade pip pyinstaller
# Install the project itself with all dependencies
pip install -e .

# Build executables
echo "Building executables..."
pyinstaller --clean --onefile --name password-manager \
    --add-data "VERSION.txt:." \
    --hidden-import=cryptography \
    apps/app.py

pyinstaller --clean --onefile --name password-manager-gui \
    --add-data "VERSION.txt:." \
    --hidden-import=cryptography \
    --hidden-import=PyQt5 \
    --hidden-import=zxcvbn \
    apps/gui.py

# Copy executables
echo "Copying executables..."
cp dist/password-manager "$DEB_DIR/opt/password-manager/bin/"
cp dist/password-manager-gui "$DEB_DIR/opt/password-manager/bin/"

# Copy documentation
echo "Copying documentation..."
cp README.md "$DEB_DIR/opt/password-manager/"
cp CHANGELOG.md "$DEB_DIR/opt/password-manager/"
cp VERSION.txt "$DEB_DIR/opt/password-manager/"
cp README.md CHANGELOG.md "$DEB_DIR/usr/share/doc/password-manager/"

if [ -d "docs" ]; then
    cp -r docs/* "$DEB_DIR/opt/password-manager/docs/" || true
fi

# Create symlinks
echo "Creating symlinks..."
cd "$DEB_DIR/usr/local/bin"
ln -s /opt/password-manager/bin/password-manager password-manager
ln -s /opt/password-manager/bin/password-manager-gui password-manager-gui
cd "$SCRIPT_DIR"

# Create desktop entry
echo "Creating desktop entry..."
cat > "$DEB_DIR/usr/share/applications/password-manager.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Secure Password Manager
Comment=Manage your passwords securely with encryption
Exec=/opt/password-manager/bin/password-manager-gui
Icon=password-manager
Terminal=false
Categories=Utility;Security;
Keywords=password;security;encryption;vault;
StartupNotify=true
EOF

# Create icon (simple SVG)
cat > "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/password-manager.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#2c3e50" rx="20"/>
  <circle cx="128" cy="100" r="40" fill="#3498db" stroke="#ecf0f1" stroke-width="4"/>
  <rect x="88" y="140" width="80" height="60" rx="8" fill="#3498db" stroke="#ecf0f1" stroke-width="4"/>
  <circle cx="128" cy="170" r="8" fill="#ecf0f1"/>
  <rect x="124" y="170" width="8" height="20" fill="#ecf0f1"/>
  <text x="128" y="230" font-family="Arial" font-size="20" font-weight="bold" fill="#ecf0f1" text-anchor="middle">PASSWORD</text>
</svg>
EOF

# Create control file
echo "Creating control file..."
cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $PACKAGE_VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: ArcheWizard <your-email@example.com>
Depends: libc6 (>= 2.27), libgcc1 (>= 1:3.0), libstdc++6 (>= 5)
Homepage: https://github.com/ArcheWizard/password-manager
Description: Secure local password manager with encryption
 Secure Password Manager is a local password management application
 that provides strong encryption, two-factor authentication, and
 comprehensive security features.
 .
 Features include:
  - AES-256 encryption via Fernet
  - PBKDF2 key derivation
  - Optional 2FA with TOTP
  - Password strength analysis
  - Breach checking
  - Secure backup and restore
  - Both CLI and GUI interfaces
EOF

# Create postinst script
cat > "$DEB_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications || true
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
fi

echo "Password Manager has been installed successfully!"
echo "Run 'password-manager-gui' to start the GUI application."
echo "Run 'password-manager' for the CLI version."

exit 0
EOF
chmod +x "$DEB_DIR/DEBIAN/postinst"

# Create prerm script
cat > "$DEB_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e
exit 0
EOF
chmod +x "$DEB_DIR/DEBIAN/prerm"

# Create postrm script
cat > "$DEB_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications || true
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
fi

echo "Password Manager has been removed."
echo "Your password data in your home directory has been preserved."

exit 0
EOF
chmod +x "$DEB_DIR/DEBIAN/postrm"

# Create copyright file
cat > "$DEB_DIR/usr/share/doc/password-manager/copyright" << 'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: password-manager
Upstream-Contact: ArcheWizard
Source: https://github.com/ArcheWizard/password-manager

Files: *
Copyright: 2024-2025 ArcheWizard
License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
EOF

# Set permissions
echo "Setting permissions..."
find "$DEB_DIR" -type d -exec chmod 755 {} \;
find "$DEB_DIR/opt/password-manager/bin" -type f -exec chmod 755 {} \;
find "$DEB_DIR/usr/share" -type f -exec chmod 644 {} \;
chmod 644 "$DEB_DIR/DEBIAN/control"

# Build the package
echo "Building .deb package..."
dpkg-deb --build "$DEB_DIR"

# Move to dist directory
mkdir -p dist
mv "${DEB_DIR}.deb" "dist/"

echo ""
echo -e "${GREEN}========================================"
echo "  .deb Package Build Complete!"
echo "========================================${NC}"
echo ""
echo "Output file: dist/${DEB_DIR}.deb"
echo ""
echo "To install:"
echo "  sudo dpkg -i dist/${DEB_DIR}.deb"
echo "  sudo apt-get install -f  # If dependencies are missing"
echo ""
echo "To uninstall:"
echo "  sudo apt remove $PACKAGE_NAME"
echo ""
echo "To distribute:"
echo "  Share the file: dist/${DEB_DIR}.deb"
echo ""
