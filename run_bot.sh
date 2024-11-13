#!/bin/bash

# Create log directory if it doesn't exist
mkdir -p /var/log/rootbot

# Run the bot in the background
nohup python3 -m root_bot > /var/log/rootbot/output.log 2> /var/log/rootbot/error.log &

# Save the PID
echo $! > /var/run/rootbot.pid

echo "RootBot started with PID $(cat /var/run/rootbot.pid)"
echo "Logs are available at /var/log/rootbot/"
echo "To stop the bot: kill $(cat /var/run/rootbot.pid)"
