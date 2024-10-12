#!/bin/bash

set -e

# Ensure we're in the correct directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

# Change to the project root directory
cd "$PROJECT_ROOT"

# Verify we're in the correct directory
if [ ! -f "package.json" ]; then
    echo "Error: Could not find package.json. Make sure you're running this script from the correct directory." >&2
    echo "Current directory: $(pwd)" >&2
    exit 1
fi

# Set the Chromium src directory
CHROMIUM_SRC_DIR="$PROJECT_ROOT/src"

# Verify the Chromium src directory exists
if [ ! -d "$CHROMIUM_SRC_DIR" ] || [ ! -f "$CHROMIUM_SRC_DIR/BUILD.gn" ]; then
    echo "Error: Could not find Chromium source directory at $CHROMIUM_SRC_DIR" >&2
    echo "Current directory structure:" >&2
    ls -R "$PROJECT_ROOT" >&2
    exit 1
fi

# Change to the Chromium src directory
cd "$CHROMIUM_SRC_DIR"

echo "Using Chromium source directory: $CHROMIUM_SRC_DIR" >&2

# Check if the 'out' directory exists, if not create it
if [ ! -d "out/Default" ]; then
  mkdir -p out/Default
fi

# Configure the build
echo "Configuring the build..." >&2
gn gen out/Default

# Run the actual build command
echo "Building Chromium..." >&2
autoninja -C out/Default chrome 2>&1 | grep -i "error:" >&2

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "Build completed successfully!" >&2
else
    echo "Build failed. See errors above." >&2
    exit 1
fi
