#!/bin/bash

# Convenience wrapper to run the build menu from the project root

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
./scripts/build_menu.sh "$@"
