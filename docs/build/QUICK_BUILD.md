# Quick Start - Linux App Building

## TL;DR - Build Your Linux App

### Interactive Menu (Easiest)

```bash
./build.sh
# or
./scripts/build_menu.sh
```

### Individual Builds

**Standalone Bundle** (Recommended):
```bash
./scripts/build_linux_app.sh
```

**AppImage** (Portable):
```bash
./scripts/build_appimage.sh
```

**Debian Package**:
```bash
./scripts/build_deb.sh
```

## What Gets Built

| Method | Output File | Size | Best For |
|--------|------------|------|----------|
| Standalone | `password-manager-v1.8.1-linux-x86_64.tar.gz` | ~50-80MB | General distribution |
| AppImage | `PasswordManager-v1.8.1-x86_64.AppImage` | ~80-100MB | Portable, no install |
| Debian | `password-manager_1.8.1_amd64.deb` | ~50-80MB | Ubuntu/Debian users |

## Testing Your Build

### Test Standalone Bundle
```bash
cd dist/password-manager-linux
./password-manager-gui        # GUI version
./password-manager            # CLI version
```

### Test AppImage
```bash
./PasswordManager-v1.8.1-x86_64.AppImage
```

### Test Debian Package
```bash
sudo dpkg -i dist/password-manager_1.8.1_amd64.deb
password-manager-gui
```

## Installation for Users

### Standalone Bundle
```bash
# Extract
tar -xzf password-manager-v1.8.1-linux-x86_64.tar.gz
cd password-manager-linux

# Install system-wide
sudo ./install.sh

# Or run directly
./password-manager-gui
```

### AppImage
```bash
# Make executable and run
chmod +x PasswordManager-v1.8.1-x86_64.AppImage
./PasswordManager-v1.8.1-x86_64.AppImage
```

### Debian Package
```bash
# Install
sudo dpkg -i password-manager_1.8.1_amd64.deb
sudo apt-get install -f  # Fix dependencies

# Run
password-manager-gui
```

## Distribution Checklist

- [ ] Build packages: `./build.sh`
- [ ] Test on clean system
- [ ] Generate checksums: `cd dist && sha256sum * > SHA256SUMS`
- [ ] Create GitHub release
- [ ] Upload packages as release assets
- [ ] Update README with download links
- [ ] Announce release

## Common Issues

**Build fails with "pyinstaller not found"**
```bash
pip install pyinstaller
```

**GUI won't start**
```bash
sudo apt install libxcb-xinerama0
```

**Permission denied**
```bash
chmod +x scripts/build_linux_app.sh
```

## File Structure After Build

```
dist/
├── password-manager-linux/          # Standalone bundle directory
│   ├── bin/
│   │   ├── password-manager         # CLI executable
│   │   └── password-manager-gui     # GUI executable
│   ├── docs/                        # Documentation
│   ├── password-manager             # CLI launcher
│   ├── password-manager-gui         # GUI launcher
│   ├── install.sh                   # Installation script
│   └── uninstall.sh                 # Uninstallation script
├── password-manager-v1.8.1-linux-x86_64.tar.gz  # Distributable archive
├── PasswordManager-v1.8.1-x86_64.AppImage       # AppImage
└── password-manager_1.8.1_amd64.deb             # Debian package
```

## Need Help?

- Full guide: `docs/build/LINUX_BUILD_GUIDE.md`
- Project docs: `docs/`
- GitHub issues: https://github.com/ArcheWizard/password-manager/issues

## Next Steps

1. **First time?** Run `./build.sh` and choose option 1
2. **Test it:** Run the built app from `dist/`
3. **Share it:** Upload to GitHub Releases
4. **Celebrate!** 🎉 You've built a Linux app!
