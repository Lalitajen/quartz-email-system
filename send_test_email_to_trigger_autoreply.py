#!/usr/bin/env python3
"""
Send a test email to jennylalita1@gmail.com to trigger auto-reply
"""

import os
import pickle
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

def send_test_email():
    """Send test email from your Gmail to trigger auto-reply"""

    print("\n🧪 Sending Test Email to Trigger Auto-Reply")
    print("="*60)

    # Load Gmail credentials
    if not os.path.exists('token.pickle'):
        print("❌ Gmail not authenticated. Run: python3 authenticate_gmail.py")
        return

    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

    gmail_service = build('gmail', 'v1', credentials=creds)

    # Get user's email
    profile = gmail_service.users().getProfile(userId='me').execute()
    from_email = profile['emailAddress']

    print(f"\n📧 Sending from: {from_email}")
    print(f"📧 Sending to: jennylalita1@gmail.com")

    # Test email content
    subject = "Interested in technical specifications"
    body = """Hi Jenny,

I'm interested in your high-purity quartz products for our glass manufacturing facility.

Can you please send me:
- Technical specifications
- ICP-MS analysis data
- Information about boron content and purity levels

We're looking for semiconductor-grade quartz with ultra-low boron content.

Thanks!"""

    print(f"\n📝 Subject: {subject}")
    print(f"📄 Body preview: {body[:100]}...")

    # Create message
    message = MIMEText(body)
    message['To'] = 'jennylalita1@gmail.com'
    message['From'] = from_email
    message['Subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    print("\n📤 Sending email...")

    try:
        sent_message = gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        print("✅ Test email sent successfully!")
        print(f"   Message ID: {sent_message['id']}")

        print("\n⏱️  Auto-reply should trigger in 5-10 seconds...")
        print("\n📊 Monitor the auto-reply daemon:")
        print("   tail -f /tmp/auto_reply.log")

        print("\n🎯 Expected Result:")
        print("   Stage: 3 (Qualification)")
        print("   PDFs: 02_Technical_Data_Sheet.pdf, 04_Detailed_Brochure.pdf")
        print("   You'll receive auto-reply at:", from_email)

        print("\n✅ Check your inbox in 10 seconds!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_test_email()
