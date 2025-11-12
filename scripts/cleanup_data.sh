#!/bin/bash
# Data cleanup script for Password Manager
# ⚠️ WARNING: This will DELETE all your passwords and settings!

set -e

echo "🗑️  Password Manager - Data Cleanup Script"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will permanently delete:"
echo "   - All stored passwords"
echo "   - Master password"
echo "   - Encryption keys"
echo "   - 2FA settings"
echo "   - All backups"
echo "   - All logs"
echo "   - All cached data"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo ""
echo "Removing data files from .data/ directory..."

# Check if .data directory exists
if [ ! -d ".data" ]; then
    echo "ℹ️  No .data directory found - nothing to clean"
    exit 0
fi

# Count files before deletion
file_count=$(find .data -type f | wc -l)
echo "📊 Found $file_count file(s) to remove"
echo ""

# Remove all files and subdirectories from .data, but keep the directory itself
if [ -d ".data" ]; then
    # Remove all contents
    find .data -mindepth 1 -delete 2>/dev/null || {
        # Fallback if find -delete doesn't work
        rm -rf .data/* .data/.[!.]* 2>/dev/null || true
    }

    # Recreate .gitkeep to maintain the directory in git
    touch .data/.gitkeep

    echo "✓ Removed all data from .data/ directory"
fi

# Also clean up logs directory if it exists at project root
if [ -d "logs" ]; then
    rm -rf logs/
    echo "✓ Removed logs/ directory"
fi

echo ""
echo "✅ Data cleanup complete!"
echo ""
echo "📁 Cleaned directories:"
echo "   - .data/ (all contents removed, directory preserved)"
if [ -d "logs" ]; then
    echo "   - logs/ (removed)"
fi
echo ""
echo "💡 Next steps:"
echo "   1. Run 'password-manager-gui' or 'password-manager'"
echo "   2. You'll be prompted to set a new master password"
echo "   3. All data files will be regenerated automatically"
echo ""
echo "🔄 The .data/ directory structure will be recreated on first run"