#!/usr/bin/env python3
"""
24/7 Automated Email Response System
Monitors Gmail every 5 seconds
Auto-replies to interested customers
Sends appropriate attachments based on pipeline stage
"""

import os
import sys
import time
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add scripts directory to path
sys.path.append('scripts')

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
CHECK_INTERVAL = 5  # Check every 5 seconds

# Pipeline stages with attachments
PIPELINE_STAGES = {
    1: {
        "name": "Prospecting",
        "attachments": ["01_Brochure.pdf"],
        "keywords": ["interested", "tell me more", "learn more", "info", "information"]
    },
    2: {
        "name": "Initial Contact",
        "attachments": ["01_Brochure.pdf", "02_Technical_Data_Sheet.pdf"],
        "keywords": ["specifications", "specs", "technical", "data sheet", "details"]
    },
    3: {
        "name": "Qualification",
        "attachments": ["02_Technical_Data_Sheet.pdf", "04_Detailed_Brochure.pdf"],
        "keywords": ["ICP-MS", "boron", "purity", "analysis", "composition", "impurities"]
    },
    4: {
        "name": "Sample & Testing",
        "attachments": ["02_Technical_Data_Sheet.pdf", "Sample_Request_Form.pdf"],
        "keywords": ["sample", "trial", "test", "2-5kg", "lab", "testing"]
    },
    5: {
        "name": "Negotiation",
        "attachments": ["03_Quotation.pdf"],
        "keywords": ["price", "quote", "quotation", "cost", "FOB", "CIF", "pricing"]
    },
    6: {
        "name": "Contract",
        "attachments": ["Contract_Template.pdf", "03_Quotation.pdf"],
        "keywords": ["contract", "agreement", "terms", "payment", "order"]
    },
    7: {
        "name": "Fulfillment",
        "attachments": ["COA.pdf", "Shipping_Docs.pdf"],
        "keywords": ["delivery", "shipping", "invoice", "COA", "shipment"]
    },
    8: {
        "name": "Follow-Up & Satisfaction",
        "attachments": ["Customer_Satisfaction_Survey.pdf"],
        "keywords": ["feedback", "satisfied", "review", "quality", "reorder"]
    },
    9: {
        "name": "Repeat Customer",
        "attachments": ["VIP_Discount_Program.pdf", "Bulk_Order_Benefits.pdf"],
        "keywords": ["repeat", "again", "more", "container", "bulk", "regular"]
    },
    10: {
        "name": "Factory Visit",
        "attachments": ["Factory_Tour_Info.pdf", "Company_Profile.pdf", "Location_Directions.pdf"],
        "keywords": ["visit", "factory", "tour", "facility", "inspection", "audit", "see", "plant", "production", "meet", "location", "address", "directions"]
    }
}

class AutoReplyDaemon:
    """24/7 Email monitoring and auto-reply system"""

    def __init__(self):
        self.gmail_service = None
        self.anthropic_client = None
        self.sheets_client = None
        self.workbook = None
        self.processed_emails = set()  # Track processed email IDs
        self.last_check_time = None

    def authenticate_gmail(self):
        """Authenticate with Gmail API"""
        print("🔐 Authenticating Gmail...")
        creds = None

        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            else:
                print("❌ Gmail not authenticated. Run: python3 authenticate_gmail.py")
                return False

        self.gmail_service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail authenticated")
        return True

    def authenticate_sheets(self):
        """Authenticate with Google Sheets"""
        print("📊 Authenticating Google Sheets...")
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
        self.sheets_client = gspread.authorize(creds)
        self.workbook = self.sheets_client.open_by_key(SPREADSHEET_ID)
        print("✅ Google Sheets authenticated")

    def initialize_anthropic(self):
        """Initialize Anthropic client"""
        print("🤖 Initializing AI...")
        self.anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
        print("✅ AI initialized")

    def get_unread_emails(self) -> List[Dict]:
        """Fetch unread emails from inbox"""
        try:
            # Get unread messages
            results = self.gmail_service.users().messages().list(
                userId='me',
                q='is:unread in:inbox',
                maxResults=10
            ).execute()

            messages = results.get('messages', [])

            unread_emails = []
            for msg in messages:
                msg_id = msg['id']

                # Skip if already processed
                if msg_id in self.processed_emails:
                    continue

                # Get full message
                message = self.gmail_service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()

                # Extract details
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')

                # Extract email address from "Name <email>" format
                if '<' in from_email:
                    email_addr = from_email.split('<')[1].split('>')[0]
                else:
                    email_addr = from_email

                # Get body
                body = self._get_email_body(message)

                unread_emails.append({
                    'id': msg_id,
                    'thread_id': message['threadId'],
                    'from': from_email,
                    'email': email_addr,
                    'subject': subject,
                    'body': body
                })

            return unread_emails

        except Exception as e:
            print(f"⚠️  Error fetching emails: {e}")
            return []

    def _get_email_body(self, message):
        """Extract email body from message"""
        try:
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                data = message['payload']['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
        except:
            pass
        return ""

    def analyze_email_with_ai(self, email_body: str) -> Dict:
        """Analyze email to detect interest and determine stage"""
        try:
            prompt = f"""Analyze this customer email and determine:
1. Interest level (HIGH/MEDIUM/LOW/NOT_INTERESTED)
2. What information they're asking for
3. Which pipeline stage they're at (1-9)

Email content:
{email_body[:1000]}

Pipeline stages:
1. Prospecting - General interest
2. Initial Contact - Want specs/details
3. Qualification - Technical questions (ICP-MS, purity, etc.)
4. Sample & Testing - Want samples
5. Negotiation - Pricing questions
6. Contract - Ready to order
7. Fulfillment - Delivery/shipping
8. Follow-Up - Feedback/satisfaction
9. Repeat Customer - Want more orders

Respond in this format:
INTEREST: [HIGH/MEDIUM/LOW/NOT_INTERESTED]
STAGE: [1-9]
REASON: [Brief explanation]"""

            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            response = message.content[0].text

            # Parse response
            lines = response.split('\n')
            interest = "MEDIUM"
            stage = 1
            reason = ""

            for line in lines:
                if line.startswith('INTEREST:'):
                    interest = line.split(':')[1].strip()
                elif line.startswith('STAGE:'):
                    try:
                        stage = int(line.split(':')[1].strip())
                    except:
                        stage = 1
                elif line.startswith('REASON:'):
                    reason = line.split(':')[1].strip()

            return {
                'interest': interest,
                'stage': stage,
                'reason': reason
            }

        except Exception as e:
            print(f"⚠️  AI analysis error: {e}")
            return {'interest': 'MEDIUM', 'stage': 1, 'reason': 'Default response'}

    def generate_auto_reply(self, email_data: Dict, analysis: Dict) -> str:
        """Generate personalized auto-reply"""
        try:
            stage_info = PIPELINE_STAGES[analysis['stage']]

            prompt = f"""Generate a professional B2B auto-reply email for:

From: {email_data['from']}
Subject: Re: {email_data['subject']}
Interest Level: {analysis['interest']}
Pipeline Stage: {stage_info['name']}

Customer's email:
{email_data['body'][:500]}

Requirements:
1. Thank them for their interest
2. Address their specific questions
3. Mention we're attaching relevant documents
4. Keep it concise (100-150 words)
5. Professional tone
6. From: {SENDER_NAME}

Documents we're attaching: {', '.join(stage_info['attachments'])}

Generate ONLY the email body (no subject line)."""

            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text.strip()

        except Exception as e:
            print(f"⚠️  Reply generation error: {e}")
            # Fallback response
            return f"""Thank you for your interest in Lorh La Seng's high-purity quartz products.

I've attached relevant documentation for your review. Our quartz offers:
• 99.5-99.89% SiO₂ purity
• Ultra-low boron (34.6 ppb)
• Semiconductor-grade quality

Please let me know if you have any questions.

Best regards,
{SENDER_NAME}
{SENDER_EMAIL}"""

    def send_auto_reply(self, to_email: str, subject: str, body: str,
                       attachments: List[str], thread_id: str) -> bool:
        """Send auto-reply with attachments"""
        try:
            # Create message
            message = MIMEMultipart()
            message['To'] = to_email
            message['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
            message['Subject'] = f"Re: {subject}"
            message['In-Reply-To'] = thread_id
            message['References'] = thread_id

            # Add body
            message.attach(MIMEText(body, 'plain'))

            # Add attachments
            for filename in attachments:
                filepath = f'attachments/{filename}'
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'pdf')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition',
                                      f'attachment; filename={filename}')
                        message.attach(part)

            # Send via Gmail API
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw, 'threadId': thread_id}
            ).execute()

            return True

        except Exception as e:
            print(f"⚠️  Send error: {e}")
            return False

    def mark_as_read(self, message_id: str):
        """Mark email as read"""
        try:
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except:
            pass

    def log_auto_reply(self, email_data: Dict, analysis: Dict, sent: bool):
        """Log auto-reply to Google Sheets"""
        try:
            # Get or create Auto Replies sheet
            try:
                sheet = self.workbook.worksheet('Auto Replies')
            except:
                sheet = self.workbook.add_worksheet(title='Auto Replies', rows=1000, cols=10)
                headers = ['timestamp', 'from_email', 'subject', 'interest_level',
                          'stage', 'attachments_sent', 'status', 'reason']
                sheet.append_row(headers)

            # Add log entry
            stage_info = PIPELINE_STAGES[analysis['stage']]
            log_entry = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                email_data['email'],
                email_data['subject'],
                analysis['interest'],
                f"{analysis['stage']} - {stage_info['name']}",
                ', '.join(stage_info['attachments']),
                'Sent' if sent else 'Failed',
                analysis['reason']
            ]
            sheet.append_row(log_entry)

        except Exception as e:
            print(f"⚠️  Logging error: {e}")

    def process_email(self, email_data: Dict):
        """Process single email"""
        print(f"\n📧 Processing email from: {email_data['from']}")
        print(f"   Subject: {email_data['subject']}")

        # Analyze with AI
        print("   🤖 Analyzing with AI...")
        analysis = self.analyze_email_with_ai(email_data['body'])
        print(f"   Interest: {analysis['interest']} | Stage: {analysis['stage']}")

        # Check if interested
        if analysis['interest'] == 'NOT_INTERESTED':
            print("   ⏭️  Not interested, skipping")
            self.mark_as_read(email_data['id'])
            self.processed_emails.add(email_data['id'])
            return

        # Generate reply
        print("   ✍️  Generating reply...")
        reply_body = self.generate_auto_reply(email_data, analysis)

        # Get attachments for stage
        stage_info = PIPELINE_STAGES[analysis['stage']]
        attachments = stage_info['attachments']
        print(f"   📎 Attaching: {', '.join(attachments)}")

        # Send reply
        print("   📤 Sending auto-reply...")
        sent = self.send_auto_reply(
            email_data['email'],
            email_data['subject'],
            reply_body,
            attachments,
            email_data['thread_id']
        )

        if sent:
            print("   ✅ Auto-reply sent!")
            self.mark_as_read(email_data['id'])
        else:
            print("   ❌ Failed to send")

        # Log
        self.log_auto_reply(email_data, analysis, sent)

        # Mark as processed
        self.processed_emails.add(email_data['id'])

    def run(self):
        """Main daemon loop - runs 24/7"""
        print("\n" + "="*70)
        print("  🤖 AUTO-REPLY DAEMON STARTING")
        print("="*70)
        print(f"  Check interval: {CHECK_INTERVAL} seconds")
        print(f"  Sender: {SENDER_NAME} <{SENDER_EMAIL}>")
        print("="*70 + "\n")

        # Authenticate everything
        if not self.authenticate_gmail():
            print("❌ Gmail authentication failed. Exiting.")
            return

        self.authenticate_sheets()
        self.initialize_anthropic()

        print("\n✅ All systems ready!")
        print("🔄 Monitoring inbox every 5 seconds...")
        print("📧 Will auto-reply to interested customers")
        print("🛑 Press Ctrl+C to stop\n")
        print("-" * 70 + "\n")

        check_count = 0

        try:
            while True:
                check_count += 1
                self.last_check_time = datetime.now()

                # Status update every 60 checks (5 minutes)
                if check_count % 60 == 0:
                    print(f"💚 System running | Checks: {check_count} | "
                          f"Processed: {len(self.processed_emails)} emails")

                # Check for new emails
                unread_emails = self.get_unread_emails()

                if unread_emails:
                    print(f"\n📬 Found {len(unread_emails)} unread email(s)")

                    for email_data in unread_emails:
                        try:
                            self.process_email(email_data)
                        except Exception as e:
                            print(f"   ❌ Error processing email: {e}")
                            # Continue with next email
                            continue

                    print()  # Blank line after processing

                # Wait before next check
                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n🛑 Stopping daemon...")
            print(f"📊 Total emails processed: {len(self.processed_emails)}")
            print("👋 Goodbye!\n")

if __name__ == "__main__":
    daemon = AutoReplyDaemon()
    daemon.run()
