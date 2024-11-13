#!/bin/bash

# Exit on error
set -e

echo "Installing RootBot..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Install required packages
apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sudo \
    logrotate \
    sysstat \
    net-tools \
    procps \
    lsof

# Install Python package
pip3 install -e .

# Create rootbot command
cp bin/rootbot /usr/local/bin/
chmod +x /usr/local/bin/rootbot

# Install and start service
rootbot install
rootbot start

echo "Installation complete!"
echo "RootBot service is now running."
echo "Check status with: rootbot status"
echo "View logs with: tail -f /var/log/rootbot/rootbot.log"

