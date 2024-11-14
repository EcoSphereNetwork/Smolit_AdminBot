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

# Create necessary directories
mkdir -p /usr/local/bin
mkdir -p models logs memory

# Install Python dependencies
pip install -r requirements.txt

# Download Llama model
echo "Downloading Llama 3.2 1B model..."
wget -O models/Llama-3.2-1B-Instruct.Q6_K.llamafile "https://huggingface.co/Mozilla/Llama-3.2-1B-Instruct-llamafile/resolve/main/Llama-3.2-1B-Instruct.Q6_K.llamafile?download=true"

# Make model executable
chmod +x models/Llama-3.2-1B-Instruct.Q6_K.llamafile

# Create symlink
ln -sf "$(pwd)/models/Llama-3.2-1B-Instruct.Q6_K.llamafile" /usr/local/bin/llamafile

# Set up permissions
./setup_permissions.sh

echo "Installation complete!"
echo "RootBot service is now running."
echo "Check status with: rootbot status"
echo "View logs with: tail -f /var/log/rootbot/rootbot.log"

