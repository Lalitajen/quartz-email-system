#!/bin/bash
# Start 24/7 Auto-Reply Daemon

echo "🚀 Starting Auto-Reply Daemon..."
echo ""

# Check prerequisites
if [ ! -f "token.pickle" ]; then
    echo "❌ Gmail not authenticated!"
    echo "   Run: python3 authenticate_gmail.py"
    exit 1
fi

if [ ! -f "service_account.json" ]; then
    echo "❌ Google Sheets credentials missing!"
    exit 1
fi

if [ ! -f "config/.env" ]; then
    echo "❌ config/.env not found!"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Start daemon in background (unbuffered output)
nohup python3 -u auto_reply_daemon.py > /tmp/auto_reply.log 2>&1 &
DAEMON_PID=$!

echo "✅ Auto-Reply Daemon started!"
echo "   PID: $DAEMON_PID"
echo "   Log: /tmp/auto_reply.log"
echo ""
echo "📊 Monitor status:"
echo "   ./monitor_status.sh"
echo ""
echo "📋 View log:"
echo "   tail -f /tmp/auto_reply.log"
echo ""
echo "🛑 Stop daemon:"
echo "   ./stop_auto_reply.sh"
echo ""
echo "System is now monitoring emails 24/7! 🎉"
