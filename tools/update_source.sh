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

# Function to show progress
show_progress() {
    local pid=$1
    local message=$2
    node -e "
        const cliProgress = require('cli-progress');
        const bar = new cliProgress.SingleBar({
            format: '${message} |{bar}| {percentage}% || {value}/{total} Chunks',
            barCompleteChar: '\u2588',
            barIncompleteChar: '\u2591',
            hideCursor: true
        });
        
        bar.start(100, 0);
        
        let progress = 0;
        const intervalId = setInterval(() => {
            if (!process.kill(${pid}, 0)) {
                clearInterval(intervalId);
                bar.update(100);
                bar.stop();
                console.log('${message} completed');
                process.exit();
            }
            progress = Math.min(progress + 1, 99);
            bar.update(progress);
        }, 1000);
    " &
    wait $pid
}

# Display welcome message
echo -e "\n${MAGENTA}=======================================${NC}"
echo -e "${MAGENTA}   Chromium Source Update Assistant${NC}"
echo -e "${MAGENTA}=======================================${NC}\n"

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
    success "Depot Tools added to PATH successfully."
else
    log "Depot Tools already in PATH."
fi

# Navigate to Chromium source directory
cd ../src || error "Chromium source directory not found. Please verify your directory structure."

# Update the source code
log "Updating Chromium source code..."
git pull &
show_progress $! "Updating Chromium source code"

# Sync dependencies
log "Syncing Chromium dependencies..."
gclient sync &
show_progress $! "Syncing Chromium dependencies"

echo -e "\n${MAGENTA}=======================================${NC}"
echo -e "${MAGENTA}   Update completed successfully!${NC}"
echo -e "${MAGENTA}   Your Chromium source code is now up-to-date!${NC}"
echo -e "${MAGENTA}=======================================${NC}\n"