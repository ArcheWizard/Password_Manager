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
if [ -f "$SCRIPT_DIR/icons/icon-16.png" ]; then
    cp "$SCRIPT_DIR/icons/"*.png "$BUILD_DIR/icons/"
elif [ -d "$SCRIPT_DIR/build/chrome/icons" ] && [ -f "$SCRIPT_DIR/build/chrome/icons/icon-16.png" ]; then
    cp "$SCRIPT_DIR/build/chrome/icons/"*.png "$BUILD_DIR/icons/"
else
    echo "Creating monochrome placeholder icons..."

    if command -v convert &> /dev/null; then
        for size in 16 32 48 128; do
            radius=$((size / 8))
            lock_body_height=$((size / 2))
            lock_body_width=$((size * 5 / 8))
            lock_body_x=$(((size - lock_body_width) / 2))
            lock_body_y=$((size / 3))
            shackle_radius=$((size / 6))
            shackle_center_x=$((size / 2))
            shackle_center_y=$((size / 4))

            convert -size ${size}x${size} xc:none \
                -fill "#111111" \
                -draw "roundrectangle 0,0 $size,$size $radius,$radius" \
                -fill white \
                -draw "roundrectangle $lock_body_x,$lock_body_y $((lock_body_x + lock_body_width)),$((lock_body_y + lock_body_height)) 2,2" \
                -fill none \
                -stroke white \
                -strokewidth 2 \
                -draw "arc $((shackle_center_x - shackle_radius)),$((shackle_center_y - shackle_radius/2)) $((shackle_center_x + shackle_radius)),$((shackle_center_y + shackle_radius)) 180,0" \
                "$BUILD_DIR/icons/icon-${size}.png" 2>/dev/null || \
            convert -size ${size}x${size} xc:none \
                -fill "#111111" \
                -draw "roundrectangle 0,0 $size,$size $radius,$radius" \
                -fill white \
                -font DejaVu-Sans-Bold \
                -pointsize $((size / 3)) \
                -gravity center \
                -annotate 0 "LK" \
                "$BUILD_DIR/icons/icon-${size}.png"
        done
    else
        python3 -c "import struct,zlib;\nfrom pathlib import Path\n\ndef png(width,height,color):\n    out=b'\\x89PNG\\r\\n\\x1a\\n'\n    ihdr=struct.pack('>IIBBBBB', width,height,8,2,0,0,0)\n    out+=struct.pack('>I',13)+b'IHDR'+ihdr+struct.pack('>I', zlib.crc32(b'IHDR'+ihdr)&0xffffffff)\n    raw=b''\n    for _ in range(height):\n        raw+=b'\\x00'+bytes(color)*width\n    data=zlib.compress(raw,9)\n    out+=struct.pack('>I', len(data))+b'IDAT'+data+struct.pack('>I', zlib.crc32(b'IDAT'+data)&0xffffffff)\n    out+=struct.pack('>I',0)+b'IEND'+struct.pack('>I', zlib.crc32(b'IEND')&0xffffffff)\n    return out\n\nbase=Path('$BUILD_DIR/icons')\nbase.mkdir(parents=True, exist_ok=True)\nfor size in (16,32,48,128):\n    (base / f'icon-{size}.png').write_bytes(png(size,size,(17,17,17)))"
    fi
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
