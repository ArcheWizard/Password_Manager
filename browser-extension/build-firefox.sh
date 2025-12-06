#!/bin/bash

# Build Firefox extension package
# Creates a distributable directory with Firefox-specific files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build/firefox"

echo "=== Building Firefox Extension ==="

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy Firefox-specific files
echo "Copying Firefox-specific files..."
cp "$SCRIPT_DIR/manifest-firefox.json" "$BUILD_DIR/manifest.json"
cp "$SCRIPT_DIR/background-firefox.js" "$BUILD_DIR/background.js"

# Copy core files
echo "Copying core files..."
cp "$SCRIPT_DIR/content.js" "$BUILD_DIR/"
cp "$SCRIPT_DIR/popup.html" "$BUILD_DIR/"
cp "$SCRIPT_DIR/popup.js" "$BUILD_DIR/"

# Create icons directory with placeholder if needed
mkdir -p "$BUILD_DIR/icons"
if [ -f "$SCRIPT_DIR/icons/icon16.png" ]; then
    cp "$SCRIPT_DIR/icons/"*.png "$BUILD_DIR/icons/"
else
    echo "Warning: No icons found. Extension will use default icons."
    echo "Add 16x16, 48x48, and 128x128 PNG icons to browser-extension/icons/"
fi

# Create README for the build
cat > "$BUILD_DIR/README.txt" << 'EOF'
Secure Password Manager - Firefox Extension
===========================================

Installation (Developer Mode):
1. Open Firefox and navigate to about:debugging
2. Click "This Firefox" in the sidebar
3. Click "Load Temporary Add-on"
4. Select the manifest.json file from this directory (build/firefox)

Pairing with Desktop App:
1. Start the Secure Password Manager desktop app
2. Open the extension popup (click the extension icon)
3. Click "Pair with Desktop App"
4. Enter the 6-digit pairing code from the desktop app
5. Click "Pair" button

Usage:
- Navigate to any login page
- Click the lock icon next to password fields
- Select credentials from the desktop app (requires approval)
- Forms are automatically monitored for saving new credentials

Note: Temporary add-ons are removed when Firefox closes.
For permanent installation, the extension needs to be signed by Mozilla.

For more information, see the main README.md
EOF

echo "✓ Firefox extension built successfully!"
echo "Location: $BUILD_DIR"
echo ""
echo "To load in Firefox:"
echo "  1. Visit about:debugging"
echo "  2. Click 'This Firefox'"
echo "  3. Click 'Load Temporary Add-on'"
echo "  4. Select: $BUILD_DIR/manifest.json"
