#!/bin/bash

# Exit on error
set -e

echo "Installing RootBot..."

# Install required packages
apt-get update && apt-get install -y supervisor

# Install Python package
pip3 install -e .

# Create necessary directories
mkdir -p /var/log/rootbot
mkdir -p /etc/rootbot

# Copy supervisor config
cp rootbot.conf /etc/supervisor/conf.d/

# Restart supervisor to load new config
supervisorctl reread
supervisorctl update

echo "Installation complete. RootBot service has been installed."
echo "To check status: supervisorctl status rootbot"
echo "To start: supervisorctl start rootbot"
echo "To stop: supervisorctl stop rootbot"

