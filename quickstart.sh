#!/bin/bash

# Quartz Email System - Quick Start Script

echo "🚀 Quartz Email Outreach System - Quick Start"
echo "============================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if (( $(echo "$python_version < 3.9" | bc -l) )); then
    echo "❌ Python 3.9+ required. Current: $python_version"
    exit 1
fi
echo "✅ Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Check for credentials
echo ""
echo "🔐 Checking credentials..."

if [ ! -f "google_credentials.json" ]; then
    echo "⚠️  google_credentials.json not found"
    echo "   → Download from Google Cloud Console"
    echo "   → Place in project root directory"
fi

if [ ! -f "gmail_credentials.json" ]; then
    echo "⚠️  gmail_credentials.json not found"
    echo "   → Download from Google Cloud Console"
    echo "   → Place in project root directory"
fi

if [ ! -f "config/.env" ]; then
    echo "⚠️  config/.env not found"
    echo "   → Copy config/.env.template to config/.env"
    echo "   → Fill in your API keys and settings"
    cp config/.env.template config/.env
    echo "   ✅ Template copied to config/.env - please edit it"
fi

echo ""
echo "📊 Next Steps:"
echo "============="
echo "1. Edit config/.env with your credentials"
echo "2. Set up Google Sheets (see SETUP_GUIDE.md)"
echo "3. Run: python scripts/main_automation.py"
echo ""
echo "📖 Read SETUP_GUIDE.md for detailed instructions"
echo ""

# Ask if user wants to run setup dashboard
read -p "Would you like to set up the Google Sheets dashboard now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your Google Sheets ID: " sheets_id
    python scripts/dashboard_setup.py "$sheets_id"
fi

echo ""
echo "🎉 Setup complete! You're ready to go."
echo ""
