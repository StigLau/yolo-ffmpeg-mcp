#!/bin/bash
# Minimal CI config script for GitHub Actions

case "$1" in
    setup)
        echo "Setting up CI environment..."
        mkdir -p /tmp/music/{source,temp,metadata,screenshots}
        exit 0
        ;;
    test)
        echo "Running CI tests..."
        exit 0
        ;;
    cleanup)
        echo "Cleaning up CI environment..."
        exit 0
        ;;
    *)
        echo "Usage: $0 {setup|test|cleanup}"
        exit 1
        ;;
esac