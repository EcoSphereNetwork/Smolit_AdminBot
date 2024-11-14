#!/bin/bash

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Stop the watchdog first
if [ -f /var/run/rootbot_watchdog.pid ]; then
    WATCHDOG_PID=$(cat /var/run/rootbot_watchdog.pid)
    if ps -p $WATCHDOG_PID > /dev/null 2>&1; then
        echo "Stopping watchdog process (PID: $WATCHDOG_PID)..."
        kill $WATCHDOG_PID
        sleep 2
    fi
    rm /var/run/rootbot_watchdog.pid
fi

# Stop the bot
if [ -f /var/run/rootbot.pid ]; then
    PID=$(cat /var/run/rootbot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping RootBot process (PID: $PID)..."
        kill $PID
        sleep 2
        
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force killing RootBot process..."
            kill -9 $PID
        fi
    fi
    rm /var/run/rootbot.pid
fi

echo "RootBot and watchdog stopped"

