#!/usr/bin/env python3
"""
Quick script to check for email replies and update tracking
"""
import os
import sys
sys.path.append('scripts')

from dotenv import load_dotenv
load_dotenv('config/.env')

from main_automation import EmailTracker, GoogleSheetsManager

def check_replies():
    """Check for new replies and update Google Sheets"""
    print("\n" + "="*60)
    print("  Checking for Email Replies")
    print("="*60 + "\n")

    # Initialize tracker
    tracker = EmailTracker('gmail_credentials.json')
    tracker.authenticate()

    print("🔍 Checking Gmail for replies in last 24 hours...")
    replies = tracker.check_new_replies(since_hours=24)

    if not replies:
        print("❌ No new replies found")
        print("   (Looking for unread emails)")
        return

    print(f"✅ Found {len(replies)} reply(ies)!\n")

    # Show replies
    for i, reply in enumerate(replies, 1):
        print(f"Reply #{i}:")
        print(f"   From: {reply['from']}")
        print(f"   Subject: {reply['subject']}")
        print(f"   Body preview: {reply['body'][:200]}...")
        print()

    # Update Google Sheets
    print("📊 Updating Google Sheets...")
    sheets = GoogleSheetsManager(os.getenv('GOOGLE_SHEETS_ID'))

    for reply in replies:
        # Extract email from "Name <email>" format
        from_email = reply['from']
        if '<' in from_email:
            from_email = from_email.split('<')[1].split('>')[0]

        print(f"   Updating status for: {from_email}")

        # Update email tracking status
        tracking_data = sheets.get_email_tracking()
        for email_log in tracking_data:
            if email_log.get('contact_email') == from_email:
                # Update status to 'replied'
                sheets.update_email_status(
                    email_log.get('email_id'),
                    'replied',
                    reply_date=reply['date']
                )
                print(f"   ✓ Updated email {email_log.get('email_id')}")

    print("\n" + "="*60)
    print("  ✓ Reply check complete!")
    print("  Refresh http://localhost:5000/tracking to see updates")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        check_replies()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()