#!/bin/bash
# Stop Auto-Reply Daemon

echo "🛑 Stopping Auto-Reply Daemon..."

# Find and kill process
PIDS=$(ps aux | grep auto_reply_daemon.py | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "ℹ️  Daemon not running"
    exit 0
fi

for PID in $PIDS; do
    kill $PID 2>/dev/null
    echo "✅ Stopped process: $PID"
done

sleep 1

# Verify stopped
if ps aux | grep auto_reply_daemon.py | grep -v grep > /dev/null; then
    echo "⚠️  Force killing..."
    killall -9 python3 2>/dev/null
fi

echo "✅ Auto-Reply Daemon stopped"
