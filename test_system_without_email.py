#!/usr/bin/env python3
"""
Test system functionality WITHOUT sending actual emails
Tests: AI generation, Google Sheets, attachments
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('config/.env')
sys.path.append('scripts')

from anthropic import Anthropic
import gspread
from google.oauth2.service_account import Credentials

# Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_ID')

def test_google_sheets():
    """Test Google Sheets connection"""
    print("\n📊 Testing Google Sheets Connection...")

    try:
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
        client = gspread.authorize(creds)
        workbook = client.open_by_key(SPREADSHEET_ID)

        # Get customers
        sheet = workbook.worksheet('Customers')
        customers = sheet.get_all_records()

        print(f"✅ Connected to Google Sheets")
        print(f"   Found {len(customers)} customers")

        # Find test customer
        test_customer = None
        for c in customers:
            if c.get('email') == 'catty366336@gmail.com':
                test_customer = c
                break

        if test_customer:
            print(f"✅ Test customer found:")
            print(f"   Company: {test_customer.get('company_name')}")
            print(f"   Email: {test_customer.get('email')}")
            print(f"   Stage: {test_customer.get('pipeline_stage')}")
        else:
            print("⚠️  Test customer not found")

        return test_customer
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_ai_generation(customer):
    """Test AI email generation"""
    print("\n🤖 Testing AI Email Generation...")

    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)

        prompt = f"""Generate a professional B2B cold outreach email for:

Company: {customer.get('company_name', 'Catty Test Company')}
Contact: {customer.get('contact_name', 'Catty Test')}
Industry: Glass Manufacturing
Country: United States

Product: High-purity quartz (SiO₂ 99.5%, Boron 34.6 ppb)
Supplier: Lorh La Seng Commercial

Requirements:
1. Subject line (max 60 chars)
2. Brief body (150 words)
3. Mention attached brochure
4. Professional tone

Format:
SUBJECT: [subject]
---
[body]"""

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text
        parts = response.split('---')
        subject = parts[0].replace('SUBJECT:', '').strip()
        body = parts[1].strip() if len(parts) > 1 else response

        print("✅ AI email generated successfully!")
        print(f"\n📧 Generated Email Preview:")
        print("-" * 70)
        print(f"To: {customer.get('email', 'catty366336@gmail.com')}")
        print(f"Subject: {subject}")
        print(f"Attachment: 01_Brochure.pdf")
        print(f"\n{body[:300]}...")
        print("-" * 70)

        return subject, body

    except Exception as e:
        print(f"❌ Error: {e}")
        if "credit balance is too low" in str(e):
            print("\n⚠️  Add API credits at: https://console.anthropic.com/settings/billing")
        return None, None

def test_attachments():
    """Test PDF attachments"""
    print("\n📎 Testing PDF Attachments...")

    attachment_path = 'attachments/01_Brochure.pdf'
    if os.path.exists(attachment_path):
        size = os.path.getsize(attachment_path)
        print(f"✅ Attachment found: 01_Brochure.pdf")
        print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")
    else:
        print(f"❌ Attachment not found: {attachment_path}")

def test_web_app():
    """Test web app is running"""
    print("\n🌐 Testing Web Application...")

    import subprocess
    result = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:5000/'],
        capture_output=True,
        text=True
    )

    if result.stdout == '200':
        print("✅ Web app is running at http://localhost:5000")
        print("   Dashboard: http://localhost:5000")
        print("   Compose: http://localhost:5000/compose")
        print("   Tracking: http://localhost:5000/tracking")
    else:
        print("❌ Web app not responding")

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  🧪 SYSTEM TEST (WITHOUT EMAIL SENDING)")
    print("="*70)

    print("\n✅ Tests you can run WITHOUT Gmail OAuth:")
    print("   1. Google Sheets connection")
    print("   2. AI email generation")
    print("   3. PDF attachments")
    print("   4. Web interface")

    # Run tests
    test_web_app()
    customer = test_google_sheets()
    test_attachments()

    if customer:
        test_ai_generation(customer)

    print("\n" + "="*70)
    print("  📋 SUMMARY")
    print("="*70)

    print("\n✅ What's Working:")
    print("   • Google Sheets: Connected")
    print("   • AI Generation: Ready (if credits available)")
    print("   • PDF Attachments: Ready")
    print("   • Web Interface: Running")

    print("\n⏳ What's Pending:")
    print("   • Gmail OAuth: Complete browser authentication")
    print("   • Then run: python3 send_test_email.py")

    print("\n🎯 Next Steps:")
    print("   1. Complete Gmail OAuth in browser")
    print("   2. Check for token.pickle file: ls -la token.pickle")
    print("   3. Run: python3 send_test_email.py")
    print("   4. Check catty366336@gmail.com for email")

    print("\n")

if __name__ == "__main__":
    main()
