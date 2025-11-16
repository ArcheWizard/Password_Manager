#!/bin/bash

# AppImage Builder for Secure Password Manager
# Creates a single-file portable Linux application

set -e

echo "========================================"
echo "  Password Manager AppImage Builder"
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
VERSION=$(cat VERSION.txt | tr -d '\n')
echo -e "${GREEN}Building AppImage for version: $VERSION${NC}"
echo ""

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

# Download appimagetool if not present
APPIMAGE_TOOL="appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGE_TOOL" ]; then
    echo "Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/$APPIMAGE_TOOL"
    chmod +x "$APPIMAGE_TOOL"
    echo -e "${GREEN}✓ appimagetool downloaded${NC}"
fi

# Create AppDir structure
APPDIR="PasswordManager.AppDir"
echo "Creating AppDir structure..."
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/doc/password-manager"

# Build with PyInstaller
echo "Building executable with PyInstaller..."
pyinstaller --clean --onefile --name password-manager-gui \
    --add-data "VERSION.txt:." \
    --add-data "README.md:." \
    --hidden-import=cryptography \
    --hidden-import=PyQt5 \
    --hidden-import=pyperclip \
    --hidden-import=pyotp \
    --hidden-import=qrcode \
    --hidden-import=requests \
    --hidden-import=zxcvbn \
    apps/gui.py

# Copy executable
echo "Copying executable to AppDir..."
cp dist/password-manager-gui "$APPDIR/usr/bin/"

# Copy documentation
cp README.md CHANGELOG.md "$APPDIR/usr/share/doc/password-manager/"

# Create AppRun script
echo "Creating AppRun script..."
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash

# AppRun script for Password Manager AppImage

SELF=$(readlink -f "$0")
HERE=${SELF%/*}

# Set up environment
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Create user data directory
mkdir -p "$HOME/.local/share/password-manager"
mkdir -p "$HOME/.config/password-manager"

# Change to user data directory
cd "$HOME/.local/share/password-manager"

# Run the application
exec "${HERE}/usr/bin/password-manager-gui" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Create desktop file
cat > "$APPDIR/password-manager.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Secure Password Manager
Comment=Manage your passwords securely
Exec=password-manager-gui
Icon=password-manager
Categories=Utility;Security;
Terminal=false
StartupNotify=true
EOF
cp "$APPDIR/password-manager.desktop" "$APPDIR/usr/share/applications/"

# Create a simple icon (PNG format)
# Note: You should replace this with a proper icon
cat > "$APPDIR/password-manager.png" << 'EOF'
#!/bin/bash
# This is a placeholder. In a real application, you would have a proper PNG icon here.
# For now, we'll use a text-based icon or you can add your own PNG file.
EOF

# If you have an icon, copy it here:
# cp path/to/your/icon.png "$APPDIR/password-manager.png"
# cp path/to/your/icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/password-manager.png"

# For now, create a simple SVG icon
cat > "$APPDIR/password-manager.svg" << 'SVGEOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#2c3e50"/>
  <circle cx="128" cy="100" r="40" fill="#3498db"/>
  <rect x="88" y="140" width="80" height="60" rx="5" fill="#3498db"/>
  <text x="128" y="210" font-family="Arial" font-size="24" fill="#ecf0f1" text-anchor="middle">PM</text>
</svg>
SVGEOF

# Convert SVG to PNG (if ImageMagick is available)
if command -v convert &> /dev/null; then
    convert "$APPDIR/password-manager.svg" "$APPDIR/password-manager.png"
    cp "$APPDIR/password-manager.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/password-manager.png"
else
    echo -e "${YELLOW}ImageMagick not found. Using SVG icon (may not display properly in all environments).${NC}"
    cp "$APPDIR/password-manager.svg" "$APPDIR/password-manager.png"
fi

# Build AppImage
echo "Building AppImage..."
ARCH=x86_64 ./"$APPIMAGE_TOOL" "$APPDIR" "PasswordManager-${VERSION}-x86_64.AppImage"

# Make it executable
chmod +x "PasswordManager-${VERSION}-x86_64.AppImage"

echo ""
echo -e "${GREEN}========================================"
echo "  AppImage Build Complete!"
echo "========================================${NC}"
echo ""
echo "Output file: PasswordManager-${VERSION}-x86_64.AppImage"
echo ""
echo "To run:"
echo "  ./PasswordManager-${VERSION}-x86_64.AppImage"
echo ""
echo "To install:"
echo "  mv PasswordManager-${VERSION}-x86_64.AppImage ~/Applications/"
echo "  chmod +x ~/Applications/PasswordManager-${VERSION}-x86_64.AppImage"
echo ""
echo "The AppImage is a single portable file that can be:"
echo "  • Run directly without installation"
echo "  • Shared with other users"
echo "  • Integrated with AppImageLauncher for desktop integration"
echo ""
