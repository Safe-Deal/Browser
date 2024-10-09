#!/bin/bash

# Ensure script is executed from the tools directory
cd "$(dirname "$0")"

# Function to log messages with enhanced UI
log() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
    exit 1
}

success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# Function to display progress bar
show_progress() {
    local duration=$1
    local steps=20
    local sleep_time=$(echo "scale=2; $duration/$steps" | bc)
    
    echo -ne "\033[1;36mProgress: ["
    for ((i=0; i<steps; i++)); do
        echo -ne "▓"
        sleep $sleep_time
    done
    echo -e "]\033[0m"
}

# ASCII art banner
echo -e "\033[1;35m"
cat << "EOF"
 ____  _   _ ___ _     ____    ____ _   _ ____   ___  __  __ ___ _   _ __  __ 
| __ )| | | |_ _| |   |  _ \  / ___| | | |  _ \ / _ \|  \/  |_ _| | | |  \/  |
|  _ \| | | || || |   | | | || |   | |_| | |_) | | | | |\/| || || | | | |\/| |
| |_) | |_| || || |___| |_| || |___|  _  |  _ <| |_| | |  | || || |_| | |  | |
|____/ \___/|___|_____|____/  \____|_| |_|_| \_\\___/|_|  |_|___|\___/|_|  |_|
EOF
echo -e "\033[0m"

# Check if depot_tools is available
if [ ! -d "../depot_tools" ]; then
    error "Depot Tools not found. Please run setup.sh first."
fi

# Add depot_tools to PATH if not already added
if [[ ":$PATH:" != *":$(pwd)/../depot_tools:"* ]]; then
    warning "Depot Tools not in PATH. Adding now..."
    export PATH="$PATH:$(pwd)/../depot_tools"
    echo 'export PATH="$PATH:'"$(pwd)/../depot_tools"'"' >> ~/.zshrc
    source ~/.zshrc
    success "Depot Tools added to PATH."
else
    log "Depot Tools already in PATH."
fi

# Navigate to Chromium source directory
cd ../src || error "Chromium source directory not found. Please verify your directory structure."

# Generate build files
log "Generating build files..."
if gn gen out/Default; then
    success "Build files generated successfully."
else
    error "Failed to generate build files"
fi

# Build Chromium
log "Building Chromium (this may take a while)..."
echo -e "\033[1;36mEstimated build time: 30-60 minutes\033[0m"
show_progress 5  # Simulating progress for 5 seconds (adjust as needed)

if ninja -C out/Default chrome; then
    success "Build completed successfully."
    log "You can find the build output in the 'out/Default' directory."
else
    error "Build failed"
fi

echo -e "\n\033[1;32m╔════════════════════════════════════════╗"
echo -e "║  Thank you for using the Chromium Builder  ║"
echo -e "╚════════════════════════════════════════╝\033[0m"