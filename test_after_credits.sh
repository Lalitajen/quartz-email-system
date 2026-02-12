#!/bin/bash
echo "🧪 Testing AI Email Generation with Credits..."
python3 test_email_generation.py

if [ $? -eq 0 ]; then
    echo ""
    echo "="
    echo "✅ SUCCESS! Your system is ready!"
    echo "="
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Restart web app: ./restart_app.sh"
    echo "   2. Go to: http://localhost:5000/compose"
    echo "   3. Select 'Catty Test Company'"
    echo "   4. Click 'Generate Email'"
    echo "   5. Email should generate successfully!"
    echo ""
else
    echo ""
    echo "⚠️  Still not working. Check billing page again."
fi
