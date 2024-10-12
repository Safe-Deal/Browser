#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
CHROMIUM_SRC_DIR="$PROJECT_ROOT/src"

echo "Setting up build environment..."

# Verify the Chromium src directory exists
if [ ! -d "$CHROMIUM_SRC_DIR" ] || [ ! -f "$CHROMIUM_SRC_DIR/BUILD.gn" ]; then
    echo "Error: Could not find Chromium source directory at $CHROMIUM_SRC_DIR"
    echo "Please ensure you have cloned the Chromium source code correctly."
    echo "Run the following commands to set up Chromium:"
    echo "  cd $PROJECT_ROOT"
    echo "  fetch chromium"
    echo "  cd src"
    echo "  gclient sync"
    exit 1
fi

# Ensure we're in the Chromium src directory
cd "$CHROMIUM_SRC_DIR"

# Verify we're in a valid Chromium checkout
if [ ! -f ".gclient" ]; then
    echo "Error: Not in a valid Chromium checkout."
    echo "Please run the following commands to set up Chromium:"
    echo "  cd $CHROMIUM_SRC_DIR"
    echo "  gclient config https://chromium.googlesource.com/chromium/src.git"
    echo "  gclient sync"
    exit 1
fi

echo "Using Chromium source directory: $CHROMIUM_SRC_DIR"

# Check if the 'out' directory exists, if not create it
if [ ! -d "out/Default" ]; then
  mkdir -p out/Default
fi

echo "Configuring the build..."
gn gen out/Default

echo "Building Chromium..."
autoninja -C out/Default chrome

if [ $? -eq 0 ]; then
    echo "Build completed successfully!"
else
    echo "Build failed. See errors above."
    exit 1
fi
