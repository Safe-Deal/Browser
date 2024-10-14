#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Treat unset variables as an error when substituting.
set -u

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

# Display welcome message
echo -e "${MAGENTA}"
echo "======================================"
echo "  Welcome to Safe Deal - Browser Setup"
echo "======================================"
echo -e "${NC}"

# Install necessary dependencies
log "Installing essential dependencies..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install python3 git cmake ninja || error "Failed to install dependencies"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update && sudo apt-get install -y python3 git cmake ninja-build || error "Failed to install dependencies"
else
    error "Unsupported operating system"
fi
success "Dependencies installed successfully."

# Clone depot_tools if not already present
if [ ! -d "../depot_tools" ]; then
    log "Cloning Depot Tools..."
    git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git ../depot_tools || error "Failed to clone depot_tools"
    success "Depot Tools cloned successfully."
else
    log "Depot Tools already cloned."
fi

# Add depot_tools to PATH
export PATH="$PATH:$(pwd)/../depot_tools"

# Function to clone Chromium repository
clone_chromium() {
    log "Cloning Chromium repository..."
    mkdir -p ../chromium
    cd ../chromium
    fetch --nohooks --no-history chromium || error "Failed to fetch Chromium"
    cd src
    git checkout main
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
        git checkout main
        git pull origin main || error "Failed to update Chromium source code"
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
cd ../chromium

# Check for local changes in problematic directories
PROBLEMATIC_DIRS=(
    "src/chrome/test/data/xr/webvr_info"
    # Add other problematic directories here if needed
)

for dir in "${PROBLEMATIC_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        cd "$dir"
        if [ -n "$(git status --porcelain)" ]; then
            log "Local changes detected in $dir. Stashing changes..."
            git stash push -m "Stashed by setup script before sync"
        fi
        cd - > /dev/null
    fi
done

# Sync dependencies
log "Running gclient sync..."
gclient sync --with_branch_heads --with_tags --no-history --nohooks || error "Failed to sync dependencies"

# Try to apply stashed changes if any
for dir in "${PROBLEMATIC_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        cd "$dir"
        if git stash list | grep -q "Stashed by setup script before sync"; then
            log "Attempting to reapply local changes in $dir..."
            if git stash apply; then
                success "Local changes in $dir reapplied successfully."
                git stash drop
            else
                warning "Conflicts occurred while reapplying local changes in $dir."
                warning "The changes are kept in the stash. Please resolve conflicts manually."
                warning "Use 'git stash show -p stash@{0}' to view the changes."
                warning "After resolving, apply changes with 'git stash pop' and commit them."
                git status
            fi
        fi
        cd - > /dev/null
    fi
done

success "Chromium dependencies synced successfully."

# Run hooks
log "Running hooks..."
gclient runhooks || error "Failed to run hooks"
success "Hooks completed successfully."

# Generate build files
log "Generating build files..."
cd src
gn gen out/Default --args='is_debug=false is_component_build=false use_jumbo_build=true symbol_level=0 blink_symbol_level=0 enable_nacl=false' || error "Failed to generate build files"
success "Build files generated successfully."

# Display completion message
echo -e "${MAGENTA}"
echo "======================================"
echo "  Setup completed successfully!"
echo "  You are ready to build Safe Deal - Browser!"
echo "======================================"
echo -e "${NC}"

success "Setup process completed. To build the browser, run: ninja -C out/Default chrome"
