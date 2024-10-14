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
NC='\033[0m' # No Color

# Function to log messages with enhanced UI
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to safely remove a directory
safe_remove_dir() {
    if [ -d "$1" ]; then
        log "Removing $1 directory..."
        rm -rf "$1" || error "Failed to remove $1 directory"
        success "$1 directory removed."
    else
        warning "$1 directory not found. Skipping..."
    fi
}

# Function to safely remove files
safe_remove_files() {
    log "Removing $1 files..."
    find .. -name "$1" -type f -delete || warning "Failed to remove some $1 files"
    success "$1 files removed."
}

# Display welcome message
echo -e "${BLUE}======================================"
echo "  Safe Deal - Browser Cleanup Script"
echo "======================================${NC}"

# Remove directories
safe_remove_dir "../chromium"
safe_remove_dir "../depot_tools"
safe_remove_dir "../out"

# Remove specific files
safe_remove_files ".gclient"
safe_remove_files ".gclient_entries"
safe_remove_files "*.pyc"
safe_remove_files "*.log"

# Clean git submodules
log "Cleaning git submodules..."
if [ -f "../.gitmodules" ]; then
    git submodule foreach --recursive git clean -fdx || warning "Failed to clean some submodules"
    git submodule foreach --recursive git reset --hard || warning "Failed to reset some submodules"
    success "Git submodules cleaned."
else
    warning ".gitmodules file not found. Skipping submodule cleaning."
fi

# Remove sync progress log
safe_remove_files "sync_progress.log"

# Final success message
echo -e "${GREEN}======================================"
echo "  Cleanup completed successfully!"
echo "======================================${NC}"
