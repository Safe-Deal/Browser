#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

echo "Cleaning nested git repositories..."

find "$PROJECT_ROOT" -type d -name ".git" | while read git_dir; do
    if [ "$git_dir" != "$PROJECT_ROOT/.git" ]; then
        echo "Removing git repository: $git_dir"
        rm -rf "$git_dir"
        echo "Git repository removed: $git_dir"
    fi
done

echo "Cleaning completed successfully!"