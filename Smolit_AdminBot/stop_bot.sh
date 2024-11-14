#!/bin/bash

if [ -f /var/run/rootbot.pid ]; then
    PID=$(cat /var/run/rootbot.pid)
    if ps -p $PID > /dev/null; then
        echo "Stopping RootBot (PID: $PID)..."
        kill $PID
        rm /var/run/rootbot.pid
        echo "RootBot stopped"
    else
        echo "RootBot not running (stale PID file)"
        rm /var/run/rootbot.pid
    fi
else
    echo "RootBot PID file not found"
fi
