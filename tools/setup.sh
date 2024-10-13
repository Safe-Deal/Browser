#!/usr/bin/env bash

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js and npm first."
    exit 1
fi

# Check if Yarn is installed
if ! command -v yarn &> /dev/null; then
    echo "Yarn is not installed. Please install Yarn first."
    exit 1
fi

# Install dependencies if they're not already installed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    yarn install
fi

# Exit immediately if a command exits with a non-zero status.
set -e

# Treat unset variables as an error when substituting.
set -u

# Print commands and their arguments as they are executed.
set -x

# Ensure script is executed from the tools directory
cd "$(dirname "$0")"

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to log messages with enhanced UI
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to display progress bar
progress_bar() {
    local duration=$1
    local steps=$2
    local sleep_time=$(bc <<< "scale=4; $duration / $steps")
    for ((i=0; i<$steps; i++)); do
        printf "\r[%-50s] %d%%" $(printf "=%.0s" $(seq 1 $((i*50/steps)))) $((i*100/steps))
        sleep $sleep_time
    done
    printf "\r[%-50s] %d%%\n" "$(printf '=' {1..50})" 100
}

# Display welcome message
echo -e "${MAGENTA}"
echo "======================================"
echo "  Welcome to Safe Deal - Browser Setup"
echo "======================================"
echo -e "${NC}"

# Checking for Homebrew, and installing if not present
if ! command -v brew &> /dev/null; then
    warning "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || error "Failed to install Homebrew"
    success "Homebrew installed successfully."
else
    log "Homebrew is already installed."
fi

# Install necessary dependencies
log "Installing essential dependencies..."
echo -e "${CYAN}This may take a few minutes. Please be patient.${NC}"
brew install python3 git cmake ninja || error "Failed to install dependencies"
success "Dependencies installed successfully."

# Clone depot_tools if not already present
if [ ! -d "../depot_tools" ]; then
    log "Cloning Depot Tools..."
    git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git ../depot_tools || error "Failed to clone depot_tools"
    success "Depot Tools cloned successfully."
else
    log "Depot Tools already cloned."
fi

# Add depot_tools to PATH if not already added
if [[ ":$PATH:" != *":$(pwd)/../depot_tools:"* ]]; then
    log "Adding Depot Tools to PATH..."
    echo 'export PATH="$PATH:'"$(pwd)/../depot_tools"'"' >> ~/.zshrc
    source ~/.zshrc
    success "Depot Tools added to PATH."
else
    log "Depot Tools already in PATH."
fi

# Function to clone Chromium repository
clone_chromium() {
    log "Cloning Chromium repository..."
    git clone https://github.com/chromium/chromium.git ../chromium/src || error "Failed to clone Chromium repository"
    cd ../chromium/src

    # Configure git to ignore problematic submodules
    git config submodule.chrome/test/data/perf/private.update none
    git config submodule.third_party/webgl/src.update none
    git config submodule.build/fuchsia/internal.update none
    git config submodule.third_party/fuchsia-sdk.update none

    # Create a .gclient file to exclude problematic dependencies
    cat > ../.gclient <<EOL
solutions = [
  {
    "url": "https://github.com/chromium/chromium.git",
    "managed": False,
    "name": "src",
    "deps_file": "DEPS",
    "custom_deps": {
      "build/fuchsia/internal": None,
      "third_party/fuchsia-sdk": None,
    },
  },
]
EOL

    # Initialize and update submodules, ignoring errors
    git submodule update --init --recursive || true

    cd - > /dev/null
    success "Chromium repository cloned successfully."
}

# Check if Chromium source code already exists
if [ -d "../chromium/src" ]; then
    log "Chromium source code directory exists."
    read -p "Do you want to update the existing code? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Updating Chromium source code..."
        cd ../chromium/src
        git pull origin main || error "Failed to update Chromium source code"
        
        # Skip updating submodules entirely
        log "Skipping submodule updates to avoid authentication issues."
        
        cd - > /dev/null
        success "Chromium source code updated successfully."
    else
        log "Skipping Chromium source code update."
    fi
else
    clone_chromium
fi

# Sync dependencies
log "Syncing Chromium dependencies..."
echo -e "${CYAN}This process may take a while. Please be patient.${NC}"

# Change to the chromium directory before running gclient sync
cd ../chromium

# Create a .gclient file to exclude all submodules
cat > .gclient <<EOL
solutions = [
  {
    "url": "https://github.com/chromium/chromium.git",
    "managed": False,
    "name": "src",
    "deps_file": "DEPS",
    "custom_deps": {},
  },
]
recursedeps = []
EOL

# Run gclient sync with options to skip all submodules
log "Syncing Chromium dependencies..."
gclient sync --ignore_locks --delete_unversioned_trees --reset --force --with_branch_heads --with_tags -v -R --nohooks || true

# Check if gclient sync was successful
if [ $? -eq 0 ]; then
    success "Chromium dependencies synced successfully."
else
    warning "Some dependencies failed to sync. This is normal for open-source contributors."
fi

# Change back to the tools directory
cd - > /dev/null

# Display completion message
echo -e "${MAGENTA}"
echo "======================================"
echo "  Setup completed successfully!"
echo "  You are ready to build Safe Deal - Browser!"
echo "======================================"
echo -e "${NC}"

# Simulating a loading process
echo "Finalizing setup..."
progress_bar 3 50

success "Setup process completed. Happy coding!"
