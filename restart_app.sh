#!/bin/bash
# Restart Quartz Email Web App

echo "🔄 Restarting Quartz Email System..."

# Stop old processes
lsof -ti :5000 | xargs kill -9 2>/dev/null
sleep 1

# Start web app
cd /Users/lalita/Downloads/quartz-email-system
python3 scripts/web_app.py > /tmp/web_app.log 2>&1 &

# Wait for startup
sleep 3

# Check if running
if curl -s http://localhost:5000/ > /dev/null 2>&1; then
    echo "✅ Web app started successfully!"
    echo "🌐 Access at: http://localhost:5000"
    echo "📎 Attachments: http://localhost:5000/attachments"
else
    echo "❌ Failed to start. Check logs:"
    tail -20 /tmp/web_app.log
fi
