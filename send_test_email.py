#!/usr/bin/env python3
"""
Send automated test email to catty366336@gmail.com
Tests: Email generation, sending, attachment, and tracking
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to path
sys.path.append('scripts')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('config/.env')

from anthropic import Anthropic
import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuthCredentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64

# Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_ID')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_NAME = os.getenv('SENDER_NAME')

# Test customer
TEST_CUSTOMER = {
    'company': 'Catty Test Company',
    'contact': 'Catty Test',
    'email': 'catty366336@gmail.com',
    'country': 'United States',
    'industry': 'Glass Manufacturing',
    'stage': 1
}

def authenticate_gmail():
    """Authenticate with Gmail API"""
    creds = None
    if os.path.exists('token.pickle'):
        import pickle
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("❌ Gmail not authenticated. Run main script first to authenticate.")
            return None

    return build('gmail', 'v1', credentials=creds)

def generate_email_with_ai(customer):
    """Generate personalized email using Claude AI"""
    print("\n🤖 Generating email with AI...")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Generate a professional B2B cold outreach email for the following prospect:

Company: {customer['company']}
Contact: {customer['contact']}
Industry: {customer['industry']}
Country: {customer['country']}
Pipeline Stage: 1 (Prospecting)

Product: High-purity quartz (SiO₂ 98.8-99.89%, Boron 34.6 ppb, Iron 0.24-0.30 ppm)
Supplier: Lorh La Seng Commercial Sole Company Limited
Capacity: 30,000-50,000 tons/month
Export via: Cua Lo Port, Vietnam

Requirements:
1. Subject line (max 60 chars)
2. Professional, concise (150-200 words)
3. Highlight ultra-low boron content (semiconductor grade)
4. Mention attached brochure
5. Clear call-to-action
6. From: {SENDER_NAME}

Format:
SUBJECT: [subject here]
---
[email body here]"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    response = message.content[0].text

    # Parse subject and body
    parts = response.split('---')
    subject = parts[0].replace('SUBJECT:', '').strip()
    body = parts[1].strip() if len(parts) > 1 else response

    print(f"✓ Email generated")
    print(f"   Subject: {subject}")

    return subject, body

def send_email_with_attachment(gmail_service, to_email, subject, body, attachment_path):
    """Send email with PDF attachment via Gmail API"""
    print(f"\n📧 Sending email to {to_email}...")

    # Create message
    message = MIMEMultipart()
    message['To'] = to_email
    message['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    message['Subject'] = subject

    # Add body
    message.attach(MIMEText(body, 'plain'))

    # Add PDF attachment
    if os.path.exists(attachment_path):
        with open(attachment_path, 'rb') as f:
            part = MIMEBase('application', 'pdf')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
            message.attach(part)
        print(f"   ✓ Attached: {os.path.basename(attachment_path)}")

    # Send via Gmail API
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        sent_message = gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        print(f"✅ Email sent successfully!")
        print(f"   Message ID: {sent_message['id']}")
        return sent_message['id']
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return None

def track_email_in_sheets(message_id, customer, subject):
    """Track sent email in Google Sheets"""
    print("\n📊 Recording email in tracking sheet...")

    # Authenticate
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
    client = gspread.authorize(creds)
    workbook = client.open_by_key(SPREADSHEET_ID)

    # Get or create Email Tracking sheet
    try:
        sheet = workbook.worksheet('Email Tracking')
    except gspread.WorksheetNotFound:
        sheet = workbook.add_worksheet(title='Email Tracking', rows=1000, cols=15)
        headers = [
            'message_id', 'customer_id', 'customer_name', 'email', 'subject',
            'sent_date', 'status', 'reply_date', 'reply_content',
            'attachments', 'stage', 'notes', 'created_at'
        ]
        sheet.append_row(headers)

    # Add tracking record
    tracking_data = [
        message_id,
        'TEST001',
        customer['company'],
        customer['email'],
        subject,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Sent',
        '',
        '',
        '01_Brochure.pdf',
        str(customer['stage']),
        'Automated test email',
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ]

    sheet.append_row(tracking_data)
    print("✓ Email tracked in Google Sheets")

def main():
    """Main test execution"""
    print("\n" + "="*70)
    print("  📧 AUTOMATED TEST EMAIL TO catty366336@gmail.com")
    print("="*70)

    # Check prerequisites
    print("\n🔍 Checking prerequisites...")

    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not found in .env")
        return
    print("✓ Anthropic API key found")

    if not os.path.exists('service_account.json'):
        print("❌ service_account.json not found")
        return
    print("✓ Google Sheets credentials found")

    if not os.path.exists('token.pickle'):
        print("❌ Gmail token.pickle not found. Run main automation first.")
        return
    print("✓ Gmail credentials found")

    attachment_path = 'attachments/01_Brochure.pdf'
    if not os.path.exists(attachment_path):
        print(f"❌ Attachment not found: {attachment_path}")
        return
    print(f"✓ Attachment found: {attachment_path}")

    # Authenticate Gmail
    gmail = authenticate_gmail()
    if not gmail:
        return
    print("✓ Gmail API authenticated")

    print("\n" + "-"*70)
    print("  STEP 1: GENERATE EMAIL")
    print("-"*70)

    # Generate email
    try:
        subject, body = generate_email_with_ai(TEST_CUSTOMER)
    except Exception as e:
        print(f"❌ Error generating email: {e}")
        if "credit balance is too low" in str(e):
            print("\n⚠️  Add credits at: https://console.anthropic.com/settings/billing")
        return

    # Preview email
    print("\n📝 Email Preview:")
    print("-" * 70)
    print(f"To: {TEST_CUSTOMER['email']}")
    print(f"Subject: {subject}")
    print(f"Attachment: 01_Brochure.pdf")
    print("\n" + body[:300] + "...")
    print("-" * 70)

    print("\n" + "-"*70)
    print("  STEP 2: SEND EMAIL")
    print("-"*70)

    # Send email
    message_id = send_email_with_attachment(
        gmail,
        TEST_CUSTOMER['email'],
        subject,
        body,
        attachment_path
    )

    if not message_id:
        print("❌ Failed to send email")
        return

    print("\n" + "-"*70)
    print("  STEP 3: TRACK EMAIL")
    print("-"*70)

    # Track in sheets
    try:
        track_email_in_sheets(message_id, TEST_CUSTOMER, subject)
    except Exception as e:
        print(f"⚠️  Warning: Could not track in sheets: {e}")

    print("\n" + "="*70)
    print("  ✅ TEST EMAIL SENT SUCCESSFULLY!")
    print("="*70)

    print("\n📋 What to do next:")
    print("   1. Check catty366336@gmail.com inbox for the email")
    print("   2. Verify 01_Brochure.pdf is attached")
    print("   3. Go to http://localhost:5000/tracking to see it tracked")
    print("   4. Reply to the email with: 'Yes, interested in technical specs'")
    print("   5. Wait 2-3 minutes for system to detect reply")
    print("   6. Check /tracking again - status should change to 'Replied'")

    print("\n🔗 Quick Links:")
    print("   Dashboard: http://localhost:5000")
    print("   Tracking:  http://localhost:5000/tracking")
    print("   Customers: http://localhost:5000/customers")

    print("\n")

if __name__ == "__main__":
    main()
