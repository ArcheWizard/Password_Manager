# Linux Application Build Guide

This guide explains how to build and distribute the Secure Password Manager as a Linux application.

## Overview

We provide three different packaging methods:

1. **Standalone Bundle** (`.tar.gz`) - Works on any Linux distribution
2. **AppImage** - Single portable file, no installation needed
3. **Debian Package** (`.deb`) - For Debian/Ubuntu-based systems

## Prerequisites

### System Requirements

- Linux system (tested on Ubuntu 20.04+, Debian 11+)
- Python 3.8 or higher
- At least 500MB free disk space
- Internet connection (for downloading tools)

### Install Build Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv python3-pip wget

# For .deb building
sudo apt install dpkg-dev

# For icon creation (optional)
sudo apt install imagemagick
```

## Build Methods

### Method 1: Standalone Bundle (Recommended for Distribution)

This creates a `.tar.gz` archive with installation scripts.

```bash
# Make the script executable
chmod +x scripts/build_linux_app.sh

# Run the build
./scripts/build_linux_app.sh
```

**Output:**
- `dist/password-manager-linux/` - Application directory
- `dist/password-manager-vX.X.X-linux-x86_64.tar.gz` - Distributable archive

**Test Locally:**
```bash
cd dist/password-manager-linux
./password-manager-gui
```

**Install System-Wide:**
```bash
cd dist/password-manager-linux
sudo ./install.sh
```

**Distribute:**
Share the `.tar.gz` file. Users extract and run:
```bash
tar -xzf password-manager-vX.X.X-linux-x86_64.tar.gz
cd password-manager-linux
sudo ./install.sh
```

### Method 2: AppImage (Single Portable File)

Creates a single executable file that runs anywhere.

```bash
chmod +x scripts/build_appimage.sh
./scripts/build_appimage.sh
```

**Output:**
- `PasswordManager-vX.X.X-x86_64.AppImage`

**Run:**
```bash
chmod +x PasswordManager-vX.X.X-x86_64.AppImage
./PasswordManager-vX.X.X-x86_64.AppImage
```

**Advantages:**
- Single file, easy to share
- No installation required
- Works on any Linux distribution
- Sandboxed execution

**Desktop Integration:**
Users can install [AppImageLauncher](https://github.com/TheAssassin/AppImageLauncher) for automatic desktop integration.

### Method 3: Debian Package

Creates a `.deb` package for Debian/Ubuntu systems.

```bash
chmod +x scripts/build_deb.sh
./scripts/build_deb.sh
```

**Output:**
- `dist/password-manager_X.X.X_amd64.deb`

**Install:**
```bash
sudo dpkg -i dist/password-manager_X.X.X_amd64.deb
sudo apt-get install -f  # Fix dependencies if needed
```

**Uninstall:**
```bash
sudo apt remove password-manager
```

**Advantages:**
- Native package management
- Automatic dependency resolution
- Clean installation/uninstallation
- Desktop integration

## Build Process Details

### What Happens During Build

1. **Virtual Environment Setup**: Creates isolated Python environment
2. **Dependency Installation**: Installs all required packages
3. **PyInstaller Compilation**: Bundles Python app with interpreter
4. **Resource Packaging**: Includes docs, icons, and config files
5. **Script Creation**: Generates installation/uninstallation scripts
6. **Archive Creation**: Packages everything for distribution

### Build Time

- First build: 5-10 minutes (downloads dependencies)
- Subsequent builds: 2-3 minutes (cached dependencies)

### Disk Space

- Build artifacts: ~300MB
- Final package: 50-80MB (compressed)

## Distribution

### Hosting Options

1. **GitHub Releases** (Recommended)
   ```bash
   # Tag your release
   git tag v1.8.1
   git push origin v1.8.1

   # Upload builds via GitHub web interface
   # Go to: Releases → Create new release → Upload assets
   ```

2. **Direct Download**
   - Host on your website
   - Use cloud storage (Dropbox, Google Drive)
   - Share via file transfer services

3. **Package Repositories**
   - Submit to [Flathub](https://flathub.org/)
   - Create PPA for Ubuntu
   - Submit to AUR for Arch Linux

### Checksum Generation

Always provide checksums for verification:

```bash
cd dist
sha256sum password-manager-*.tar.gz > SHA256SUMS
sha256sum PasswordManager-*.AppImage >> SHA256SUMS
sha256sum password-manager_*.deb >> SHA256SUMS
```

Users verify with:
```bash
sha256sum -c SHA256SUMS
```

## Installation Instructions for Users

### For Standalone Bundle

```bash
# Download and extract
tar -xzf password-manager-vX.X.X-linux-x86_64.tar.gz
cd password-manager-linux

# Option 1: Install system-wide
sudo ./install.sh

# Option 2: Run without installing
./password-manager-gui
```

### For AppImage

```bash
# Download
wget https://yoursite.com/PasswordManager-vX.X.X-x86_64.AppImage

# Make executable
chmod +x PasswordManager-vX.X.X-x86_64.AppImage

# Run
./PasswordManager-vX.X.X-x86_64.AppImage
```

### For .deb Package

```bash
# Download
wget https://yoursite.com/password-manager_X.X.X_amd64.deb

# Install
sudo dpkg -i password-manager_X.X.X_amd64.deb
sudo apt-get install -f  # Fix any missing dependencies

# Run
password-manager-gui
```

## Troubleshooting

### Build Errors

**Error: `pyinstaller: command not found`**
```bash
pip install pyinstaller
```

**Error: `No module named 'PyQt5'`**
```bash
pip install -r requirements.txt
```

**Error: Permission denied**
```bash
chmod +x scripts/build_linux_app.sh
```

### Runtime Errors

**Error: `cannot execute binary file`**
```bash
chmod +x password-manager-gui
```

**Error: GUI doesn't start**
```bash
# Install missing X11 libraries
sudo apt install libxcb-xinerama0 libxcb-cursor0
```

**Error: `libffi.so.7: cannot open shared object file`**
```bash
# Install missing library
sudo apt install libffi7
```

### Common Issues

1. **AppImage won't run on older systems**
   - Solution: Use standalone bundle instead
   - Or: Update system libraries

2. **Desktop entry doesn't appear**
   - Solution: Log out and log back in
   - Or: Run `update-desktop-database ~/.local/share/applications`

3. **Permission issues with data files**
   - Solution: Run from home directory
   - Data stored in current working directory

## Advanced Topics

### Custom Icon

Replace the default icon:

```bash
# Create or download your icon (256x256 PNG)
cp your-icon.png password-manager-icon.png

# Edit build scripts to use your icon
# Look for icon-related sections in scripts/build_*.sh files
```

### Cross-Compilation

To build for different architectures:

```bash
# Install cross-compilation tools
sudo apt install qemu-user-static

# Build for ARM64
ARCH=aarch64 ./scripts/build_linux_app.sh
```

### Automated Builds

Set up GitHub Actions for automatic builds:

```yaml
# .github/workflows/build.yml
name: Build Linux Apps
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build
        run: ./build_linux_app.sh
      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: linux-builds
          path: dist/*
```

### Signing Packages

Sign your packages for added security:

```bash
# For .deb packages
dpkg-sig --sign builder password-manager_*.deb

# For AppImage
gpg --detach-sign --armor PasswordManager-*.AppImage
```

## File Locations

### Installed Files

**System-wide installation:**
- Binaries: `/opt/password-manager/`
- Symlinks: `/usr/local/bin/`
- Desktop entry: `/usr/share/applications/`
- Icons: `/usr/share/icons/hicolor/`
- Docs: `/usr/share/doc/password-manager/`

**User data:**
- Database: `~/passwords.db` (or current directory)
- Config: `~/.config/password-manager/`
- Logs: `~/logs/` (or current directory)

### Build Artifacts

- `build/` - Temporary build files (can be deleted)
- `dist/` - Final build outputs
- `*.spec` - PyInstaller specification files
- `venv/` - Virtual environment (can be deleted after build)

## Support

### Getting Help

- GitHub Issues: https://github.com/ArcheWizard/password-manager/issues
- Documentation: `docs/` directory
- README: `README.md`

### Reporting Build Issues

Include this information:
- Your Linux distribution and version: `lsb_release -a`
- Python version: `python3 --version`
- Error messages
- Build log output

## Next Steps

1. **Build your first package:** Start with the standalone bundle
2. **Test thoroughly:** Try installation on a clean system
3. **Create checksums:** Generate SHA256SUMS file
4. **Upload to GitHub:** Create a release with your builds
5. **Announce:** Share with users and community

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [AppImage Documentation](https://docs.appimage.org/)
- [Debian Packaging Guide](https://www.debian.org/doc/manuals/maint-guide/)
- [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/)

---

**Happy Building! 🚀**
