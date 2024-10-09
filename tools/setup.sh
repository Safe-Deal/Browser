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

# Checking for Homebrew, and installing if not present
if ! command -v brew &> /dev/null; then
    log "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || error "Failed to install Homebrew"
else
    log "Homebrew is already installed."
fi

# Install necessary dependencies
log "Installing essential dependencies..."
brew install python3 git cmake ninja || error "Failed to install dependencies"

# Clone depot_tools if not already present
if [ ! -d "../depot_tools" ]; then
    log "Cloning Depot Tools..."
    git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git ../depot_tools || error "Failed to clone depot_tools"
else
    log "Depot Tools already cloned."
fi

# Add depot_tools to PATH if not already added
if [[ ":$PATH:" != *":$(pwd)/../depot_tools:"* ]]; then
    log "Adding Depot Tools to PATH..."
    echo 'export PATH="$PATH:'"$(pwd)/../depot_tools"'"' >> ~/.zshrc
    source ~/.zshrc
else
    log "Depot Tools already in PATH."
fi

# Fetch Chromium source code
log "Fetching Chromium source code..."
fetch --nohooks chromium || error "Failed to fetch Chromium source code"

# Sync dependencies
log "Syncing Chromium dependencies..."
gclient sync || error "Failed to sync Chromium dependencies"

log "Setup completed successfully. You are ready to build Safe Deal - Browser!"