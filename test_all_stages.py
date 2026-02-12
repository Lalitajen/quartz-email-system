#!/usr/bin/env python3
"""
Send test emails for all pipeline stages
Watch PDFs change automatically
"""

import os
import pickle
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

# Test scenarios for each stage
TEST_SCENARIOS = [
    {
        "stage": 1,
        "name": "Prospecting",
        "subject": "Interested in your company",
        "body": "Hi, I came across your company and I'm interested in learning more about your products.",
        "expected_pdfs": ["01_Brochure.pdf"]
    },
    {
        "stage": 2,
        "name": "Initial Contact",
        "subject": "Request for specifications",
        "body": "Hello, can you please send me the technical specifications and data sheets for your quartz products?",
        "expected_pdfs": ["01_Brochure.pdf", "02_Technical_Data_Sheet.pdf"]
    },
    {
        "stage": 3,
        "name": "Qualification",
        "subject": "Question about purity and boron content",
        "body": "We need detailed ICP-MS analysis data. What's the boron content and purity level of your quartz?",
        "expected_pdfs": ["02_Technical_Data_Sheet.pdf", "04_Detailed_Brochure.pdf"]
    },
    {
        "stage": 4,
        "name": "Sample Request",
        "subject": "Sample for laboratory testing",
        "body": "We'd like to order a 2-5kg sample for laboratory testing. Can you send the sample request form?",
        "expected_pdfs": ["02_Technical_Data_Sheet.pdf", "Sample_Request_Form.pdf"]
    },
    {
        "stage": 5,
        "name": "Pricing",
        "subject": "Request for quotation",
        "body": "What are your prices? We need a quotation with FOB and CIF costs for bulk orders.",
        "expected_pdfs": ["03_Quotation.pdf"]
    },
    {
        "stage": 6,
        "name": "Contract",
        "subject": "Ready to place order",
        "body": "We're ready to place an order. Please send the contract and payment terms.",
        "expected_pdfs": ["Contract_Template.pdf", "03_Quotation.pdf"]
    },
    {
        "stage": 7,
        "name": "Shipping",
        "subject": "Shipment status",
        "body": "When will our order arrive? Can you send the COA and shipping documents?",
        "expected_pdfs": ["COA.pdf", "Shipping_Docs.pdf"]
    },
    {
        "stage": 8,
        "name": "Feedback",
        "subject": "Product feedback",
        "body": "We received the shipment. Can you send a satisfaction survey? We'd like to provide feedback.",
        "expected_pdfs": ["Customer_Satisfaction_Survey.pdf"]
    },
    {
        "stage": 9,
        "name": "Repeat Order",
        "subject": "Bulk order inquiry",
        "body": "We want to place another bulk order. Do you have volume discounts for container loads?",
        "expected_pdfs": ["VIP_Discount_Program.pdf", "Bulk_Order_Benefits.pdf"]
    }
]

def send_test_emails():
    """Send test emails for all stages"""

    print("\n" + "="*70)
    print("  🧪 TESTING ALL PIPELINE STAGES")
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
    print(f"\n⏱️  Will send 9 emails (one per stage) with 3 second delay\n")

    sent_count = 0

    for scenario in TEST_SCENARIOS:
        print(f"\n{'─'*70}")
        print(f"📨 Test {scenario['stage']}/9: {scenario['name']}")
        print(f"{'─'*70}")
        print(f"Subject: {scenario['subject']}")
        print(f"Body: {scenario['body'][:60]}...")
        print(f"Expected PDFs: {', '.join(scenario['expected_pdfs'])}")

        # Create message
        message = MIMEText(scenario['body'])
        message['To'] = 'jennylalita1@gmail.com'
        message['From'] = from_email
        message['Subject'] = scenario['subject']

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        try:
            sent_message = gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            print(f"✅ Sent! Message ID: {sent_message['id'][:20]}...")
            sent_count += 1

            # Wait between emails
            if scenario['stage'] < 9:
                print("   Waiting 3 seconds...")
                time.sleep(3)

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "="*70)
    print(f"  ✅ SENT {sent_count}/9 TEST EMAILS")
    print("="*70)

    print("\n⏱️  Auto-replies will be sent in 5-45 seconds...")
    print("\n📊 Watch the daemon process them:")
    print("   tail -f /tmp/auto_reply.log")

    print("\n🎯 What Will Happen:")
    print("   • Daemon will find 9 unread emails")
    print("   • AI will analyze each one")
    print("   • Different PDFs attached for each stage:")

    for scenario in TEST_SCENARIOS:
        print(f"     Stage {scenario['stage']}: {', '.join(scenario['expected_pdfs'])}")

    print("\n📬 Check your inbox in 1 minute:")
    print(f"   You'll have 9 auto-replies with different PDFs!")

    print("\n✨ This demonstrates the system automatically changes PDFs")
    print("   based on what the customer asks for!\n")

if __name__ == "__main__":
    send_test_emails()
