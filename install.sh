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
    lsof \
    supervisor

# Install Python package
pip3 install -e .

# Create necessary directories
mkdir -p /var/log/rootbot
mkdir -p /etc/rootbot

# Copy supervisor config
cp rootbot.conf /etc/supervisor/conf.d/

# Set up permissions and user
./setup_permissions.sh

# Run configuration validation
echo "Validating configuration..."
python3 -c "
from root_bot.config_validator import ConfigValidator
validator = ConfigValidator()
is_valid, errors, warnings = validator.validate_config()
if not is_valid:
    print('Configuration errors:', errors)
    exit(1)
for warning in warnings:
    print('Warning:', warning)
"

# Run tests
echo "Running tests..."
python3 test_bot.py

# Restart supervisor to load new config
supervisorctl reread
supervisorctl update

echo "Installation complete!"
echo "To start RootBot, run: ./run_bot.sh"
echo "To stop RootBot, run: ./stop_bot.sh"
echo "Check logs in /var/log/rootbot/"

