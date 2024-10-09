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

# Check if Chromium source code already exists
if [ -d "../src" ]; then
    log "Chromium source code directory already exists."
    read -p "Do you want to update the existing code? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Updating Chromium source code..."
        cd ../src
        git pull origin main || error "Failed to update Chromium source code"
        cd - > /dev/null
        success "Chromium source code updated successfully."
    else
        read -p "Do you want to force a fresh fetch? This will delete the existing source code. (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Removing existing Chromium source code..."
            rm -rf ../src
            log "Fetching Chromium source code..."
            echo -e "${CYAN}This process may take a while. Feel free to grab a coffee!${NC}"
            fetch --nohooks chromium || error "Failed to fetch Chromium source code"
            success "Chromium source code fetched successfully."
        else
            log "Skipping Chromium source code fetch/update."
        fi
    fi
else
    log "Fetching Chromium source code..."
    echo -e "${CYAN}This process may take a while. Feel free to grab a coffee!${NC}"
    fetch --nohooks chromium || error "Failed to fetch Chromium source code"
    success "Chromium source code fetched successfully."
fi

# Sync dependencies
log "Syncing Chromium dependencies..."
echo -e "${CYAN}This process may take a while. Please be patient.${NC}"

# Function to show progress
show_progress() {
    local pid=$1
    local message=$2
    local timeout=3600  # 1 hour timeout

    node -e "
        const cliProgress = require('cli-progress');
        const fs = require('fs');
        const bar = new cliProgress.SingleBar({
            format: '${message} |{bar}| {percentage}% || {value}/{total} Chunks || Elapsed: {duration_formatted}',
            barCompleteChar: '\u2588',
            barIncompleteChar: '\u2591',
            hideCursor: true
        });
        
        bar.start(100, 0);
        
        let progress = 0;
        let lastUpdateTime = Date.now();
        const startTime = Date.now();
        const logFile = 'sync_progress.log';

        const intervalId = setInterval(() => {
            if (!process.kill(${pid}, 0)) {
                clearInterval(intervalId);
                bar.update(100);
                bar.stop();
                console.log('${message} completed');
                process.exit();
            }

            const currentTime = Date.now();
            if (currentTime - startTime > ${timeout} * 1000) {
                clearInterval(intervalId);
                bar.stop();
                console.log('${message} timed out after ${timeout} seconds');
                process.exit(1);
            }

            if (currentTime - lastUpdateTime > 10000) {  // Log every 10 seconds
                fs.appendFileSync(logFile, \`\${new Date().toISOString()}: Progress at \${progress}%\n\`);
                lastUpdateTime = currentTime;
            }

            progress = Math.min(progress + 0.1, 99);
            bar.update(progress);
        }, 1000);
    " &
    wait $pid
    if [ $? -ne 0 ]; then
        error "The ${message} process failed or timed out. Check sync_progress.log for details."
    fi
}

# Usage example:
log "Syncing Chromium dependencies..."
gclient sync &
show_progress $! "Syncing Chromium dependencies"

# Check if gclient sync was successful
if [ $? -eq 0 ]; then
    success "Chromium dependencies synced successfully."
else
    error "Failed to sync Chromium dependencies"
fi

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