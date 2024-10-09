#!/bin/bash

# Ensure script is executed from the tools directory
cd "$(dirname "$0")"

# Define color codes for better UI
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages with enhanced UI
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Function to display progress bar
show_progress() {
    local duration=$1
    local steps=20
    local sleep_time=$(echo "scale=2; $duration / $steps" | bc)
    
    echo -ne "${YELLOW}Progress: ${NC}"
    for ((i=0; i<steps; i++)); do
        echo -ne "${GREEN}█${NC}"
        sleep $sleep_time
    done
    echo -e "\n"
}

# Display welcome message
echo -e "\n${GREEN}=======================================${NC}"
echo -e "${GREEN}   Chromium Source Update Assistant${NC}"
echo -e "${GREEN}=======================================${NC}\n"

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
    log "Depot Tools added to PATH successfully."
else
    log "Depot Tools already in PATH."
fi

# Navigate to Chromium source directory
cd ../safe-deal-browser/src || error "Chromium source directory not found. Please verify your directory structure."

# Update the source code
log "Updating Chromium source code..."
show_progress 5
git pull || error "Failed to update Chromium source code"

# Sync dependencies
log "Syncing Chromium dependencies..."
show_progress 10
gclient sync || error "Failed to sync dependencies"

echo -e "\n${GREEN}=======================================${NC}"
echo -e "${GREEN}   Update completed successfully!${NC}"
echo -e "${GREEN}   Your Chromium source code is now up-to-date!${NC}"
echo -e "${GREEN}=======================================${NC}\n"