#!/usr/bin/env python3
"""
Send test email to customer: catty366336@gmail.com
With appropriate attachments based on their inquiry
"""

import os
import pickle
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64

def send_to_customer():
    """Send email with attachments to customer"""

    print("\n📧 Sending Email to Customer: catty366336@gmail.com")
    print("="*70)

    # Load Gmail credentials
    if not os.path.exists('token.pickle'):
        print("❌ Gmail not authenticated. Run: python3 authenticate_gmail.py")
        return

    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

    gmail_service = build('gmail', 'v1', credentials=creds)

    # Email content
    to_email = "catty366336@gmail.com"
    subject = "High-Purity Quartz Products - Technical Information"

    body = """Dear Catty,

Thank you for your interest in Lorh La Seng's high-purity quartz products!

I'm pleased to share detailed technical information about our semiconductor-grade quartz:

KEY SPECIFICATIONS:
• SiO₂ Purity: 99.5-99.89% (Grade A)
• Boron Content: 34.6 ppb (ultra-low, semiconductor grade)
• Iron (Fe₂O₃): 0.24-0.30 ppm (exceptional optical clarity)
• Capacity: 30,000-50,000 tons/month

APPLICATIONS:
• Semiconductor manufacturing
• Solar panel production
• Optical fiber
• Specialty glass

I've attached our technical data sheet and detailed brochure for your review.
These documents include:
- Complete ICP-MS analysis
- Chemical composition tables
- Application guidelines
- Quality certifications

Please feel free to reach out if you have any questions or would like to discuss
your specific requirements. We're here to help!

Best regards,

Jenny Lalita
Business Development Manager
Lorh La Seng Commercial Sole Company Limited

Email: jennylalita1@gmail.com
Phone: +856 20 xxxx xxxx
Export via: Cua Lo Port, Vietnam
Website: www.lorhquartz.com

---
This email was sent by Lorh La Seng Commercial Sole Company Limited, Vientiane, Laos.
If you wish to unsubscribe, please reply with "UNSUBSCRIBE".
We respect your privacy and comply with GDPR and CAN-SPAM regulations."""

    # PDFs to attach (Stage 3 - Qualification)
    attachments = [
        "02_Technical_Data_Sheet.pdf",
        "04_Detailed_Brochure.pdf"
    ]

    print(f"\n📧 To: {to_email}")
    print(f"📝 Subject: {subject}")
    print(f"📎 Attachments: {', '.join(attachments)}")

    # Create message
    message = MIMEMultipart()
    message['To'] = to_email
    message['From'] = 'Jenny Lalita <jennylalita1@gmail.com>'
    message['Subject'] = subject

    # Add body
    message.attach(MIMEText(body, 'plain'))

    # Add PDF attachments
    attached_count = 0
    for filename in attachments:
        filepath = f'attachments/{filename}'
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'pdf')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={filename}')
                message.attach(part)
                print(f"   ✅ Attached: {filename} ({os.path.getsize(filepath)/1024:.1f} KB)")
                attached_count += 1
        else:
            print(f"   ⚠️  Missing: {filename}")

    if attached_count == 0:
        print("\n❌ No attachments found!")
        return

    print(f"\n📤 Sending email...")

    try:
        # Send via Gmail API
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent_message = gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        print("✅ Email sent successfully!")
        print(f"   Message ID: {sent_message['id']}")

        print("\n📬 Check catty366336@gmail.com inbox!")
        print("   You should receive:")
        print("   • Professional email from Jenny Lalita")
        print("   • 02_Technical_Data_Sheet.pdf (4.4 KB)")
        print("   • 04_Detailed_Brochure.pdf (4.4 KB)")

        print("\n✅ This is how the auto-reply system sends to real customers!")
        print("   Same format, same attachments, same professionalism.")

    except Exception as e:
        print(f"❌ Error sending email: {e}")

if __name__ == "__main__":
    send_to_customer()
