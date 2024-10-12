#!/bin/bash

set -e

echo "Building Chromium (this may take a while)..."

# Ensure we're in the correct directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

# Change to the project root directory
cd "$PROJECT_ROOT"

# Verify we're in the correct directory
if [ ! -f "package.json" ]; then
    echo "Error: Could not find package.json. Make sure you're running this script from the correct directory."
    echo "Current directory: $(pwd)"
    exit 1
fi

# Try to find the Chromium src directory
CHROMIUM_SRC_DIR=""
for dir in "$PROJECT_ROOT" "$PROJECT_ROOT/.." "$PROJECT_ROOT/../.."; do
    if [ -d "$dir/src" ] && [ -f "$dir/src/BUILD.gn" ]; then
        CHROMIUM_SRC_DIR="$dir/src"
        break
    fi
done

if [ -z "$CHROMIUM_SRC_DIR" ]; then
    echo "Error: Could not find Chromium source directory."
    echo "Current directory structure:"
    ls -R "$PROJECT_ROOT"
    exit 1
fi

# Change to the Chromium src directory
cd "$CHROMIUM_SRC_DIR"

echo "Using Chromium source directory: $CHROMIUM_SRC_DIR"

# Check if the 'out' directory exists, if not create it
if [ ! -d "out/Default" ]; then
  mkdir -p out/Default
fi

# Configure the build
echo "Configuring the build..."
gn gen out/Default

# Run the actual build command
echo "Building Chromium..."
autoninja -C out/Default chrome

echo "Build completed successfully!"
