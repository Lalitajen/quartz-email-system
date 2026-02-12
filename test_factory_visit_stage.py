#!/usr/bin/env python3
"""
Test Factory Visit Stage (Stage 10)
Send email requesting factory visit to trigger auto-reply
"""

import os
import pickle
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

def test_factory_visit():
    """Send test email about factory visit"""

    print("\n" + "="*70)
    print("  🏭 TESTING FACTORY VISIT STAGE (Stage 10)")
    print("="*70)

    # Load Gmail credentials
    if not os.path.exists('token.pickle'):
        print("❌ Gmail not authenticated. Run: python3 authenticate_gmail.py")
        return

    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

    gmail_service = build('gmail', 'v1', credentials=creds)
    profile = gmail_service.users().getProfile(userId='me').execute()
    from_email = profile['emailAddress']

    print(f"\n📧 Sending from: {from_email}")
    print(f"📧 Sending to: jennylalita1@gmail.com")

    # Test email content for factory visit
    subject = "Request for Factory Visit and Tour"
    body = """Dear Jenny,

We are very interested in your high-purity quartz products and would like to visit your factory facility in Laos.

We would like to:
• Tour the production facility
• See the quality control laboratory
• Meet with your technical team
• Inspect the production process
• Discuss potential long-term partnership

Could you please provide:
1. Factory location and directions
2. Available dates for factory tour
3. Company profile information
4. What we can expect to see during the visit

We're planning to visit Vientiane next month and would love to schedule a factory inspection at your plant.

Looking forward to meeting your team!

Best regards,
Potential Customer"""

    print(f"\n📝 Subject: {subject}")
    print(f"📄 Body preview: {body[:100]}...")

    # Create message
    message = MIMEText(body)
    message['To'] = 'jennylalita1@gmail.com'
    message['From'] = from_email
    message['Subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    print("\n📤 Sending test email...")

    try:
        sent_message = gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        print("✅ Test email sent successfully!")
        print(f"   Message ID: {sent_message['id']}")

        print("\n⏱️  Auto-reply should trigger in 5-45 seconds...")
        print("\n📊 Monitor the daemon:")
        print("   tail -f /tmp/auto_reply.log")

        print("\n🎯 Expected Result:")
        print("   Stage: 10 (Factory Visit)")
        print("   PDFs:")
        print("     • Factory_Tour_Info.pdf")
        print("     • Company_Profile.pdf")
        print("     • Location_Directions.pdf")
        print(f"\n   Auto-reply will be sent to: {from_email}")

        print("\n✅ Check your inbox in 1 minute!")
        print("   You should receive a professional response with factory visit details")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_factory_visit()
