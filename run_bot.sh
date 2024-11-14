#!/bin/bash

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if the bot is already running
if [ -f /var/run/rootbot.pid ]; then
    PID=$(cat /var/run/rootbot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "RootBot is already running with PID $PID"
        exit 1
    else
        echo "Removing stale PID file"
        rm /var/run/rootbot.pid
    fi
fi

# Create log directory if it doesn't exist
mkdir -p /var/log/rootbot

# Run the bot in the background
nohup python3 -m root_bot > /var/log/rootbot/output.log 2> /var/log/rootbot/error.log &

# Save the PID
echo $! > /var/run/rootbot.pid

echo "RootBot started with PID $(cat /var/run/rootbot.pid)"
echo "Logs are available at /var/log/rootbot/"
echo "To stop the bot: kill $(cat /var/run/rootbot.pid)"

# Start the watchdog process
echo "Starting RootBot watchdog..."
python3 watchdog.py > logs/watchdog_stdout.log 2>&1 &
WATCHDOG_PID=$!

# Save watchdog PID
echo $WATCHDOG_PID > /var/run/rootbot_watchdog.pid
echo "Watchdog started with PID $WATCHDOG_PID"

