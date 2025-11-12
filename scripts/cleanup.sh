#!/bin/bash
# Cleanup script for Password Manager build artifacts and temporary files
# Run this to clean up development environment

set -e  # Exit on error

echo "🧹 Password Manager - Cleanup Script"
echo "====================================="
echo ""

# Track what we're doing
CLEANED=()
KEPT=()

# Function to remove directory if it exists
cleanup_dir() {
    local dir="$1"
    local reason="$2"

    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        echo "🗑️  Removing $dir ($size) - $reason"
        rm -rf "$dir"
        CLEANED+=("$dir")
    else
        echo "✓  $dir - already clean"
    fi
}

# Function to check if directory should be kept
check_dir() {
    local dir="$1"
    if [ -d "$dir" ]; then
        KEPT+=("$dir")
    fi
}

echo "Cleaning build artifacts..."
echo ""

# Remove temporary build directories
cleanup_dir "build" "PyInstaller build cache"
cleanup_dir "dist" "Distribution files (can be rebuilt)"
cleanup_dir "temp_restore" "Temporary restore directory"
cleanup_dir "secure_password_manager.egg-info" "Outdated packaging metadata"

# Remove Python cache
cleanup_dir ".pytest_cache" "Pytest cache"
cleanup_dir ".ruff_cache" "Ruff linter cache"

# Clean up __pycache__ recursively
echo ""
echo "Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -exec rm -f {} + 2>/dev/null || true
find . -type f -name "*.pyo" -exec rm -f {} + 2>/dev/null || true

echo ""
echo "Checking important directories are preserved..."
check_dir ".data"
check_dir "src"
check_dir "tests"
check_dir "docs"
check_dir "scripts"
check_dir "assets"

echo ""
echo "✅ Cleanup complete!"
echo ""
if [ ${#CLEANED[@]} -gt 0 ]; then
    echo "Removed: ${CLEANED[*]}"
fi
echo ""
echo "💡 Tip: These directories are regenerated automatically:"
echo "   - build/     - Created by PyInstaller"
echo "   - dist/      - Created by build scripts"
echo "   - *.egg-info - Created by pip install"
echo ""
echo "🔄 To rebuild: Run your build scripts in scripts/ directory"
