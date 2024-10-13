#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

cd "$PROJECT_ROOT/chromium/src"

echo "Updating Chromium source code..."
git pull origin main

echo "Syncing Chromium dependencies..."
gclient sync

echo "Update completed successfully!"
