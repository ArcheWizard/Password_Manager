#!/bin/bash

# Build all browser extension packages

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==================================="
echo "Building All Browser Extensions"
echo "==================================="
echo ""

# Build Chrome extension
bash "$SCRIPT_DIR/build-chrome.sh"
echo ""

# Build Firefox extension
bash "$SCRIPT_DIR/build-firefox.sh"
echo ""

echo "==================================="
echo "All builds completed successfully!"
echo "==================================="
echo ""
echo "Build locations:"
echo "  Chrome:  $SCRIPT_DIR/build/chrome/"
echo "  Firefox: $SCRIPT_DIR/build/firefox/"
echo ""
echo "For packaging .crx or .xpi files, see docs/browser-extension-packaging.md"
