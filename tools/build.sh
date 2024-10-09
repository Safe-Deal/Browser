#!/bin/bash

# Ensure script is executed from the tools directory
cd "$(dirname "$0")"

# Function to log messages with UX enhancement
log() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
    exit 1
}

# Check if depot_tools is available
if [ ! -d "../depot_tools" ]; then
    error "Depot Tools not found. Please run setup.sh first."
fi

# Add depot_tools to PATH if not already added
if [[ ":$PATH:" != *":$(pwd)/../depot_tools:"* ]]; then
    log "Adding Depot Tools to PATH..."
    export PATH="$PATH:$(pwd)/../depot_tools"
    echo 'export PATH="$PATH:'"$(pwd)/../depot_tools"'"' >> ~/.zshrc
    source ~/.zshrc
else
    log "Depot Tools already in PATH."
fi

# Navigate to Chromium source directory
cd ../src || error "Chromium source directory not found. Please verify your directory structure."

# Generate build files
log "Generating build files..."
gn gen out/Default || error "Failed to generate build files"

# Build Chromium
log "Building Chromium (this may take a while)..."
ninja -C out/Default chrome || error "Build failed"

log "Build completed successfully. You can find the build output in the 'out/Default' directory."