# Build Documentation

This directory contains comprehensive documentation for building and packaging the Password Manager application for Linux.

## Quick Links

- **[BUILD_SUMMARY.md](BUILD_SUMMARY.md)** - Complete overview of the build system
- **[QUICK_BUILD.md](QUICK_BUILD.md)** - Quick reference and commands
- **[LINUX_BUILD_GUIDE.md](LINUX_BUILD_GUIDE.md)** - Comprehensive build guide

## Getting Started

To build your Linux application packages:

```bash
# From project root
./build.sh

# Or directly
./scripts/build_menu.sh
```

## Build Methods

The build system supports three packaging formats:

1. **Standalone Bundle** - `.tar.gz` archive with installation scripts
2. **AppImage** - Single portable executable file
3. **Debian Package** - `.deb` package for Ubuntu/Debian

## Documentation Files

### BUILD_SUMMARY.md
Complete overview including:
- What has been created
- How to use the build system
- Distribution guidelines
- Troubleshooting

### QUICK_BUILD.md
Quick reference guide with:
- TL;DR build commands
- Testing instructions
- Common issues and fixes
- Distribution checklist

### LINUX_BUILD_GUIDE.md
Comprehensive guide covering:
- Detailed build process
- Prerequisites and dependencies
- Distribution hosting options
- Advanced topics (signing, CI/CD)
- User installation instructions

## Build Scripts Location

All build scripts are located in the `scripts/` directory at the project root:

- `scripts/build_linux_app.sh` - Standalone bundle builder
- `scripts/build_appimage.sh` - AppImage builder
- `scripts/build_deb.sh` - Debian package builder
- `scripts/build_menu.sh` - Interactive menu

## Quick Commands

```bash
# Build all packages
./build.sh

# Build standalone bundle
./scripts/build_linux_app.sh

# Build AppImage
./scripts/build_appimage.sh

# Build Debian package
./scripts/build_deb.sh

# Clean build artifacts
rm -rf build/ dist/ *.AppDir/
```

## Support

For issues or questions:
- Check the troubleshooting sections in the guides
- Review project documentation in `docs/`
- Open an issue on GitHub

---

**Need more details?** Start with [BUILD_SUMMARY.md](BUILD_SUMMARY.md) for a complete overview.
