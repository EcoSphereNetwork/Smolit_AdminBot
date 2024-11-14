#!/bin/bash

# Setup AppArmor profile for RootBot
setup_apparmor() {
    echo "Setting up AppArmor profile..."
    
    # Check if AppArmor is installed
    if ! command -v apparmor_parser &> /dev/null; then
        echo "AppArmor not found. Installing..."
        apt-get update && apt-get install -y apparmor apparmor-utils
    fi
    
    # Copy profile to AppArmor directory
    cp rootbot.apparmor /etc/apparmor.d/rootbot
    
    # Load the profile
    apparmor_parser -r /etc/apparmor.d/rootbot
    
    # Enable the profile
    aa-enforce rootbot
    
    echo "AppArmor profile installed and enforced"
}

# Set secure file permissions
secure_permissions() {
    echo "Setting secure file permissions..."
    
    # Set ownership
    chown -R root:root .
    
    # Set directory permissions
    find . -type d -exec chmod 750 {} \;
    
    # Set file permissions
    find . -type f -exec chmod 640 {} \;
    
    # Make scripts executable
    chmod 750 *.sh
    chmod 750 run_bot.sh
    chmod 750 stop_bot.sh
    
    # Protect sensitive files
    chmod 600 rootbot.conf
    chmod 600 root_bot/config/config.py
    
    echo "File permissions secured"
}

# Main setup
echo "Starting security setup..."

# Run setup functions
setup_apparmor
secure_permissions

echo "Security setup completed"
