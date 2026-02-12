#!/bin/bash
# Stop Auto Reply Monitor

echo "🛑 Stopping Auto Reply Monitor..."
pkill -f "auto_reply_monitor.py"

sleep 1

if pgrep -f "auto_reply_monitor.py" > /dev/null; then
    echo "⚠️  Process still running, forcing stop..."
    pkill -9 -f "auto_reply_monitor.py"
fi

echo "✅ Auto Reply Monitor stopped"