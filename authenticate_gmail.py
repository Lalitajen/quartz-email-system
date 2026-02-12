#!/usr/bin/env python3
"""
Complete Gmail OAuth authentication
Creates token.pickle for email sending
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """Authenticate with Gmail API"""
    creds = None

    # Check for existing token
    if os.path.exists('token.pickle'):
        print("✓ Found existing Gmail token")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If credentials are invalid or don't exist, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Starting Gmail OAuth flow...")
            print("   A browser window will open")
            print("   Sign in with: jennylalita1@gmail.com")
            print("   Grant access to send/read emails")

            flow = InstalledAppFlow.from_client_secrets_file(
                'gmail_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            print("✅ Authentication successful!")

        # Save credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        print("✓ Token saved to token.pickle")

    # Test the connection
    print("\n🧪 Testing Gmail connection...")
    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    print(f"✅ Connected to Gmail: {profile['emailAddress']}")
    print(f"   Total messages: {profile.get('messagesTotal', 0)}")

    return service

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Gmail OAuth Authentication")
    print("="*60 + "\n")

    try:
        authenticate_gmail()
        print("\n" + "="*60)
        print("  ✓ Gmail authentication complete!")
        print("  You can now send emails")
        print("="*60 + "\n")
    except FileNotFoundError:
        print("❌ gmail_credentials.json not found")
        print("   Make sure the file exists in current directory")
    except Exception as e:
        print(f"❌ Error: {e}")
