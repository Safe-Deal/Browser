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

# ... (rest of the initial setup)

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

# ... (rest of the script)

# Build Chromium
log "Building Chromium (this may take a while)..."
ninja -C out/Default chrome &
show_progress $! "Building Chromium"

# ... (rest of the script)