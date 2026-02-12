#!/bin/bash
# Start Auto Reply Monitor in background

cd "$(dirname "$0")"

# Check if already running
if pgrep -f "auto_reply_monitor.py" > /dev/null; then
    echo "⚠️  Auto Reply Monitor is already running"
    echo "   Use ./stop_monitor.sh to stop it first"
    exit 1
fi

# Start the monitor
echo "🚀 Starting Auto Reply Monitor..."
nohup python3 auto_reply_monitor.py > logs/auto_reply_monitor.log 2>&1 &
PID=$!

sleep 2

if ps -p $PID > /dev/null; then
    echo "✅ Auto Reply Monitor started (PID: $PID)"
    echo "   Checking for replies every 24 hours"
    echo "   Log file: logs/auto_reply_monitor.log"
    echo ""
    echo "   To stop: ./stop_monitor.sh"
    echo "   To view logs: tail -f logs/auto_reply_monitor.log"
else
    echo "❌ Failed to start monitor"
    exit 1
fi