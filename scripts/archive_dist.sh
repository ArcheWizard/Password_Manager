#!/bin/bash
# Archive distribution files before cleanup
# This moves dist/ to a releases/ directory for safekeeping

set -e

ARCHIVE_DIR="releases"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -d "dist" ]; then
    echo "📦 Archiving distribution files..."
    mkdir -p "$ARCHIVE_DIR"

    # Create timestamped archive
    mv dist "$ARCHIVE_DIR/dist_$TIMESTAMP"

    echo "✅ Archived to: $ARCHIVE_DIR/dist_$TIMESTAMP"
    echo ""
    echo "💡 Add 'releases/' to .gitignore if you don't want to track these."
else
    echo "ℹ️  No dist/ directory to archive"
fi
