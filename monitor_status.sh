#!/bin/bash
# Monitor Auto-Reply Daemon Status

clear
echo "═══════════════════════════════════════════════════════════"
echo "  📊 AUTO-REPLY DAEMON STATUS"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if running
if ps aux | grep auto_reply_daemon.py | grep -v grep > /dev/null; then
    PID=$(ps aux | grep auto_reply_daemon.py | grep -v grep | awk '{print $2}')
    UPTIME=$(ps -p $PID -o etime= | tr -d ' ')
    echo "✅ Status: RUNNING"
    echo "   PID: $PID"
    echo "   Uptime: $UPTIME"
else
    echo "❌ Status: NOT RUNNING"
    echo ""
    echo "Start with: ./start_auto_reply.sh"
    exit 0
fi

echo ""
echo "───────────────────────────────────────────────────────────"
echo "  📧 RECENT ACTIVITY (Last 20 lines)"
echo "───────────────────────────────────────────────────────────"

if [ -f "/tmp/auto_reply.log" ]; then
    tail -20 /tmp/auto_reply.log | grep -E "Processing|Sent|Found|Interest|System running" || echo "No recent activity"
else
    echo "No log file found"
fi

echo ""
echo "───────────────────────────────────────────────────────────"
echo "  🎯 STATISTICS"
echo "───────────────────────────────────────────────────────────"

if [ -f "/tmp/auto_reply.log" ]; then
    PROCESSED=$(grep -c "Processing email" /tmp/auto_reply.log 2>/dev/null || echo "0")
    SENT=$(grep -c "Auto-reply sent!" /tmp/auto_reply.log 2>/dev/null || echo "0")
    FAILED=$(grep -c "Failed to send" /tmp/auto_reply.log 2>/dev/null || echo "0")

    echo "📨 Total Processed: $PROCESSED"
    echo "✅ Successfully Sent: $SENT"
    echo "❌ Failed: $FAILED"
else
    echo "No statistics available"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  📋 COMMANDS"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  View live log:    tail -f /tmp/auto_reply.log"
echo "  Stop daemon:      ./stop_auto_reply.sh"
echo "  Restart daemon:   ./stop_auto_reply.sh && ./start_auto_reply.sh"
echo ""
echo "  Press Ctrl+R to refresh this status"
echo ""
