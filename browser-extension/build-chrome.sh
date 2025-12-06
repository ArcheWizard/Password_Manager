#!/bin/bash

# Build Chrome extension package
# Creates a distributable directory with Chrome-specific files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build/chrome"
ICONS_SRC="$SCRIPT_DIR/icons"

echo "=== Building Chrome Extension ==="

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy core files
echo "Copying core files..."
cp "$SCRIPT_DIR/manifest.json" "$BUILD_DIR/"
cp "$SCRIPT_DIR/background.js" "$BUILD_DIR/"
cp "$SCRIPT_DIR/content.js" "$BUILD_DIR/"
cp "$SCRIPT_DIR/popup.html" "$BUILD_DIR/"
cp "$SCRIPT_DIR/popup.js" "$BUILD_DIR/"

# Create icons directory
mkdir -p "$BUILD_DIR/icons"

# Check if source icons exist
ICONS_EXIST=false
for size in 16 32 48 128; do
    if [ -f "$ICONS_SRC/icon-${size}.png" ]; then
        ICONS_EXIST=true
        break
    fi
done

if [ "$ICONS_EXIST" = true ]; then
    echo "Copying existing icons..."
    cp "$ICONS_SRC/"*.png "$BUILD_DIR/icons/"
else
    echo "Creating placeholder icons..."

    # Check for ImageMagick
    if command -v convert &> /dev/null; then
        echo "Using ImageMagick to generate high-quality icons..."

        # Create icons with lock symbol
        for size in 16 32 48 128; do
            # Calculate proportions
            padding=$((size / 8))
            radius=$((size / 8))
            lock_body_height=$((size / 2))
            lock_body_width=$((size * 5 / 8))
            lock_body_x=$(((size - lock_body_width) / 2))
            lock_body_y=$((size / 3))
            shackle_radius=$((size / 6))
            shackle_center_x=$((size / 2))
            shackle_center_y=$((size / 4))

            # Create icon with rounded rectangle background and lock
            convert -size ${size}x${size} xc:none \
                -fill "#4CAF50" \
                -draw "roundrectangle 0,0 $size,$size $radius,$radius" \
                -fill white \
                -draw "roundrectangle $lock_body_x,$lock_body_y $((lock_body_x + lock_body_width)),$((lock_body_y + lock_body_height)) 2,2" \
                -fill none \
                -stroke white \
                -strokewidth 2 \
                -draw "arc $((shackle_center_x - shackle_radius)),$((shackle_center_y - shackle_radius/2)) $((shackle_center_x + shackle_radius)),$((shackle_center_y + shackle_radius)) 180,0" \
                "$BUILD_DIR/icons/icon-${size}.png" 2>/dev/null || \
            # Fallback: simple icon with text
            convert -size ${size}x${size} xc:none \
                -fill "#4CAF50" \
                -draw "roundrectangle 0,0 $size,$size $radius,$radius" \
                -fill white \
                -font DejaVu-Sans-Bold \
                -pointsize $((size / 3)) \
                -gravity center \
                -annotate 0 "PM" \
                "$BUILD_DIR/icons/icon-${size}.png"
        done

        echo "✓ Created high-quality placeholder icons"
        echo ""
        echo "💡 To use custom icons, add them to: $ICONS_SRC/"
        echo "   Required sizes: icon-16.png, icon-32.png, icon-48.png, icon-128.png"

    else
        echo "⚠️  ImageMagick not found - creating minimal placeholders"
        echo ""
        echo "To install ImageMagick:"
        echo "  sudo apt install imagemagick  # Ubuntu/Debian"
        echo "  brew install imagemagick       # macOS"
        echo ""

        # Create minimal valid PNG files as fallback
        # These are single-pixel PNGs that will at least let the extension load
        for size in 16 32 48 128; do
            # Create a simple green square PNG
            python3 -c "
import struct
import zlib

def create_png(width, height, color):
    # PNG signature
    png = b'\\x89PNG\\r\\n\\x1a\\n'

    # IHDR chunk
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    png += struct.pack('>I', 13)  # IHDR length
    png += b'IHDR' + ihdr
    png += struct.pack('>I', zlib.crc32(b'IHDR' + ihdr) & 0xffffffff)

    # IDAT chunk - solid color
    raw_data = b''
    for y in range(height):
        raw_data += b'\\x00'  # Filter type
        for x in range(width):
            raw_data += bytes(color)  # RGB

    compressed = zlib.compress(raw_data, 9)
    png += struct.pack('>I', len(compressed))
    png += b'IDAT' + compressed
    png += struct.pack('>I', zlib.crc32(b'IDAT' + compressed) & 0xffffffff)

    # IEND chunk
    png += struct.pack('>I', 0)
    png += b'IEND'
    png += struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff)

    return png

# Green color for Password Manager
color = (76, 175, 80)  # #4CAF50
png_data = create_png($size, $size, color)

with open('$BUILD_DIR/icons/icon-${size}.png', 'wb') as f:
    f.write(png_data)
"
        done

        echo "✓ Created minimal placeholder icons"
        echo ""
        echo "⚠️  WARNING: Using minimal placeholder icons"
        echo "   Install ImageMagick for better icons, or add custom icons to:"
        echo "   $ICONS_SRC/"
    fi
fi

# Verify all required icons exist
MISSING_ICONS=()
for size in 16 32 48 128; do
    if [ ! -f "$BUILD_DIR/icons/icon-${size}.png" ]; then
        MISSING_ICONS+=($size)
    fi
done

if [ ${#MISSING_ICONS[@]} -gt 0 ]; then
    echo ""
    echo "❌ ERROR: Missing required icon sizes: ${MISSING_ICONS[*]}"
    echo "   Extension may not load properly in Chrome."
    exit 1
fi

# Create README for the build
cat > "$BUILD_DIR/README.txt" << 'EOF'
Secure Password Manager - Chrome Extension
==========================================

Installation (Developer Mode):
1. Open Chrome and navigate to chrome://extensions/
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" button
4. Select this directory (build/chrome)

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

For more information, see the main README.md
EOF

echo ""
echo "✓ Chrome extension built successfully!"
echo "Location: $BUILD_DIR"
echo ""
echo "📦 Build includes:"
echo "   - Core files: manifest.json, background.js, content.js, popup.*"
echo "   - Icons: 16x16, 32x32, 48x48, 128x128"
echo ""
echo "To load in Chrome:"
echo "  1. Visit chrome://extensions/"
echo "  2. Enable 'Developer mode'"
echo "  3. Click 'Load unpacked'"
echo "  4. Select: $BUILD_DIR"