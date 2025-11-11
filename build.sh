#!/bin/bash

# Convenience wrapper to run the build menu from the root directory

cd "$(dirname "$0")"
./scripts/build_menu.sh "$@"
