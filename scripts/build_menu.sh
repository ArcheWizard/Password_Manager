#!/bin/bash

# Quick build script - Choose your build method

set -e

# Get script directory and move to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Password Manager Linux App Builder  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Display version
if [ -f "VERSION.txt" ]; then
    VERSION=$(cat VERSION.txt | tr -d '\n')
    echo -e "${GREEN}Version: $VERSION${NC}"
    echo ""
fi

# Menu
echo "Choose a build method:"
echo ""
echo "  1) Standalone Bundle (.tar.gz)"
echo "     → Best for general distribution"
echo "     → Works on any Linux distribution"
echo "     → Includes installation scripts"
echo ""
echo "  2) AppImage"
echo "     → Single portable file"
echo "     → No installation needed"
echo "     → Run anywhere"
echo ""
echo "  3) Debian Package (.deb)"
echo "     → For Ubuntu/Debian systems"
echo "     → Native package management"
echo "     → Clean installation"
echo ""
echo "  4) Build All"
echo "     → Creates all package types"
echo ""
echo "  5) Clean Build Artifacts"
echo "     → Remove all build files"
echo ""
echo "  0) Exit"
echo ""

read -p "Enter your choice [0-5]: " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}Building Standalone Bundle...${NC}"
        chmod +x scripts/build_linux_app.sh
        ./scripts/build_linux_app.sh
        ;;
    2)
        echo ""
        echo -e "${GREEN}Building AppImage...${NC}"
        chmod +x scripts/build_appimage.sh
        ./scripts/build_appimage.sh
        ;;
    3)
        echo ""
        echo -e "${GREEN}Building Debian Package...${NC}"
        chmod +x scripts/build_deb.sh
        ./scripts/build_deb.sh
        ;;
    4)
        echo ""
        echo -e "${GREEN}Building All Packages...${NC}"
        echo ""

        echo -e "${YELLOW}[1/3] Building Standalone Bundle...${NC}"
        chmod +x scripts/build_linux_app.sh
        ./scripts/build_linux_app.sh

        echo ""
        echo -e "${YELLOW}[2/3] Building AppImage...${NC}"
        chmod +x scripts/build_appimage.sh
        ./scripts/build_appimage.sh

        echo ""
        echo -e "${YELLOW}[3/3] Building Debian Package...${NC}"
        chmod +x scripts/build_deb.sh
        ./scripts/build_deb.sh        echo ""
        echo -e "${GREEN}All packages built successfully!${NC}"
        ;;
    5)
        echo ""
        echo -e "${YELLOW}Cleaning build artifacts...${NC}"
        rm -rf build/
        rm -rf dist/
        rm -rf *.AppDir/
        rm -rf password-manager_*_amd64/
        rm -f *.spec
        rm -f appimagetool-*.AppImage
        echo -e "${GREEN}Cleanup complete!${NC}"
        ;;
    0)
        echo ""
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo ""
        echo -e "${YELLOW}Invalid choice. Please run again.${NC}"
        exit 1
        ;;
esac

# Display results if build was successful
if [ $choice -ge 1 ] && [ $choice -le 4 ]; then
    echo ""
    echo -e "${GREEN}═════════════════════════════════════${NC}"
    echo -e "${GREEN}  Build Complete!${NC}"
    echo -e "${GREEN}═════════════════════════════════════${NC}"
    echo ""

    if [ -d "dist" ]; then
        echo "Output files:"
        ls -lh dist/ 2>/dev/null || true
        echo ""
    fi

    echo "Next steps:"
    echo "  • Test: cd dist/password-manager-linux && ./password-manager-gui"
    echo "  • Install: cd dist/password-manager-linux && sudo ./install.sh"
    echo "  • Distribute: Share files from dist/ directory"
    echo ""
    echo "For detailed instructions, see: docs/build/LINUX_BUILD_GUIDE.md"
    echo ""
fi
