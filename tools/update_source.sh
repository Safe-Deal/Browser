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

# Adding depot_tools to PATH if not already added
if [[ ":$PATH:" != *":$(pwd)/../depot_tools:"* ]]; then
    log "Adding Depot Tools to PATH..."
    export PATH="$PATH:$(pwd)/../depot_tools"
    echo 'export PATH="$PATH:'"$(pwd)/../depot_tools"'"' >> ~/.zshrc
    source ~/.zshrc
else
    log "Depot Tools already in PATH."
fi

# Navigate to Chromium source directory
cd ../safe-deal-browser/src || error "Chromium source directory not found. Please verify your directory structure."

# Update the source code
log "Updating Chromium source code..."
git pull || error "Failed to update Chromium source code"

# Sync dependencies
log "Syncing Chromium dependencies..."
gclient sync || error "Failed to sync dependencies"

log "Update completed successfully. Your Chromium source code is now up-to-date!"