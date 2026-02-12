"""
Advanced Automated Email Workflow System
- Automated sending with approval
- Intelligent follow-ups
- Customer segmentation by behavior
- AI-powered engagement analysis
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import anthropic
import requests
from bs4 import BeautifulSoup
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
GOOGLE_SHEETS_ID = os.environ.get('GOOGLE_SHEETS_ID', '')

# Customer Engagement Levels
ENGAGEMENT_LEVELS = {
    'HOT': {
        'criteria': ['replied_multiple', 'requested_quote', 'requested_sample', 'requested_meeting'],
        'priority': 1,
        'follow_up_days': 1,
        'action': 'Immediate personal attention'
    },
    'WARM': {
        'criteria': ['opened_email', 'clicked_link', 'replied_once', 'asked_questions'],
        'priority': 2,
        'follow_up_days': 3,
        'action': 'Send additional information'
    },
    'INTERESTED': {
        'criteria': ['opened_email', 'viewed_multiple_times'],
        'priority': 3,
        'follow_up_days': 5,
        'action': 'Gentle follow-up'
    },
    'COLD': {
        'criteria': ['no_open', 'no_response'],
        'priority': 4,
        'follow_up_days': 7,
        'action': 'Different approach needed'
    },
    'UNRESPONSIVE': {
        'criteria': ['multiple_attempts', 'no_engagement'],
        'priority': 5,
        'follow_up_days': 14,
        'action': 'Pause or remove'
    }
}


class CustomerSegmentationEngine:
    """Analyze customer behavior and segment by engagement"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def analyze_customer_engagement(self, customer: Dict, email_history: List[Dict]) -> Dict:
        """Analyze customer's engagement level and intent"""
        
        # Collect engagement signals
        signals = {
            'emails_sent': len(email_history),
            'emails_opened': sum(1 for e in email_history if e.get('opened') == 'yes'),
            'emails_replied': sum(1 for e in email_history if e.get('replied') == 'yes'),
            'last_interaction': self._get_last_interaction_date(email_history),
            'reply_content': self._extract_reply_content(email_history),
            'current_stage': customer.get('pipeline_stage', 1)
        }
        
        # AI analysis of engagement
        analysis_prompt = f"""Analyze this B2B customer's engagement level for quartz export business.

Customer: {customer.get('company_name')}
Industry: {customer.get('industry', 'Unknown')}

Engagement Data:
- Total emails sent: {signals['emails_sent']}
- Emails opened: {signals['emails_opened']}
- Times replied: {signals['emails_replied']}
- Last interaction: {signals['last_interaction']}
- Current pipeline stage: {signals['current_stage']}

Recent replies:
{signals['reply_content'][:500] if signals['reply_content'] else 'No replies yet'}

Analyze and provide:
1. engagement_level: HOT/WARM/INTERESTED/COLD/UNRESPONSIVE
2. buying_intent: high/medium/low/none
3. next_action: Specific recommendation
4. pain_points: What they care about
5. urgency_score: 1-10 (10 = needs immediate attention)
6. recommended_message: What type of message to send next
7. key_interests: What they've shown interest in

Format as JSON."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            response_text = message.content[0].text
            
            # Extract JSON
            if '{' in response_text and '}' in response_text:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                analysis = json.loads(response_text[json_start:json_end])
            else:
                analysis = self._default_analysis()
            
            # Add raw signals
            analysis['signals'] = signals
            analysis['analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Engagement analysis failed: {e}")
            return self._default_analysis()
    
    def _get_last_interaction_date(self, email_history: List[Dict]) -> str:
        """Get last interaction date"""
        if not email_history:
            return "Never"
        
        dates = []
        for email in email_history:
            if email.get('sent_date'):
                dates.append(email['sent_date'])
            if email.get('reply_date'):
                dates.append(email['reply_date'])
        
        if dates:
            latest = max(dates)
            days_ago = (datetime.now() - datetime.strptime(latest, '%Y-%m-%d')).days
            return f"{days_ago} days ago"
        return "Never"
    
    def _extract_reply_content(self, email_history: List[Dict]) -> str:
        """Extract reply content from email history"""
        replies = []
        for email in email_history:
            if email.get('reply_content_summary'):
                replies.append(email['reply_content_summary'])
        return ' | '.join(replies) if replies else ""
    
    def _default_analysis(self) -> Dict:
        """Default analysis structure"""
        return {
            'engagement_level': 'INTERESTED',
            'buying_intent': 'medium',
            'next_action': 'Send follow-up',
            'pain_points': 'Needs assessment',
            'urgency_score': 5,
            'recommended_message': 'value_proposition',
            'key_interests': []
        }


class AutomatedEmailSender:
    """Handle automated email sending with smart scheduling"""
    
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self.service = None
        
    def authenticate(self):
        """Authenticate with Gmail API"""
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        SCOPES = ['https://www.googleapis.com/auth/gmail.send',
                  'https://www.googleapis.com/auth/gmail.readonly']
        
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def send_email(self, to: str, subject: str, body: str, attachments: List[str] = None) -> bool:
        """Send email via Gmail API"""
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'html'))
            
            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        self._attach_file(message, filepath)
            
            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            send_message = {'raw': raw_message}
            
            self.service.users().messages().send(userId='me', body=send_message).execute()
            print(f"✅ Email sent to {to}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to}: {e}")
            return False
    
    def _attach_file(self, message: MIMEMultipart, filepath: str):
        """Attach file to email"""
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(filepath)}')
            message.attach(part)


class FollowUpManager:
    """Manage automated follow-up sequences"""
    
    def __init__(self, api_key: str, sheets_manager, email_sender):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.sheets = sheets_manager
        self.sender = email_sender
    
    def identify_follow_ups_needed(self) -> List[Dict]:
        """Identify customers who need follow-up"""
        customers = self.sheets.get_customers()
        email_tracking = self.sheets.get_all_emails()
        
        follow_ups = []
        
        for customer in customers:
            customer_emails = [e for e in email_tracking if e.get('customer_id') == customer.get('id')]
            
            if not customer_emails:
                continue
            
            last_email = max(customer_emails, key=lambda x: x.get('sent_date', ''))
            
            # Check if follow-up needed
            if self._needs_follow_up(customer, last_email):
                follow_up_info = {
                    'customer': customer,
                    'last_email': last_email,
                    'days_since_last': self._days_since(last_email.get('sent_date')),
                    'reason': self._get_follow_up_reason(customer, last_email)
                }
                follow_ups.append(follow_up_info)
        
        return follow_ups
    
    def _needs_follow_up(self, customer: Dict, last_email: Dict) -> bool:
        """Determine if customer needs follow-up"""
        # No response after initial email
        if last_email.get('status') == 'sent' and last_email.get('replied') != 'yes':
            days_since = self._days_since(last_email.get('sent_date'))
            
            # Different follow-up timings based on engagement
            stage = customer.get('pipeline_stage', 1)
            
            if stage == 1 and days_since >= 3:  # Prospecting
                return True
            elif stage == 2 and days_since >= 5:  # Initial Contact
                return True
            elif stage >= 3 and days_since >= 7:  # Later stages
                return True
        
        return False
    
    def _days_since(self, date_str: str) -> int:
        """Calculate days since date"""
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            return (datetime.now() - date).days
        except:
            return 0
    
    def _get_follow_up_reason(self, customer: Dict, last_email: Dict) -> str:
        """Get reason for follow-up"""
        if last_email.get('opened') == 'yes' and last_email.get('replied') != 'yes':
            return "Opened but no reply"
        elif last_email.get('opened') != 'yes':
            return "Not opened"
        else:
            return "General follow-up"
    
    def generate_follow_up_email(self, customer: Dict, last_email: Dict, reason: str) -> Dict:
        """Generate contextual follow-up email"""
        
        prompt = f"""Generate a follow-up email for this B2B quartz export prospect.

Customer: {customer.get('company_name')}
Industry: {customer.get('industry', 'Manufacturing')}
Pipeline Stage: {customer.get('pipeline_stage')}

Previous Email:
Subject: {last_email.get('subject')}
Sent: {last_email.get('sent_date')}
Opened: {last_email.get('opened', 'no')}
Replied: {last_email.get('replied', 'no')}

Follow-up Reason: {reason}

Generate a professional follow-up email that:
1. References previous email naturally
2. Adds new value (insight, case study, or offer)
3. Creates urgency without being pushy
4. Has clear, easy call-to-action
5. Keeps it brief (100-150 words)

Format as JSON with keys: subject, body, tone_note"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            if '{' in response_text and '}' in response_text:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                email_data = json.loads(response_text[json_start:json_end])
            else:
                email_data = {
                    'subject': f"Re: {last_email.get('subject', 'Quartz Supply')}",
                    'body': response_text,
                    'tone_note': 'Professional follow-up'
                }
            
            return email_data
            
        except Exception as e:
            print(f"⚠️ Follow-up generation failed: {e}")
            return None


class SmartWorkflowOrchestrator:
    """Orchestrate the entire automated workflow"""
    
    def __init__(self, sheets_id: str, api_key: str):
        self.sheets = GoogleSheetsManager(sheets_id)
        self.segmentation = CustomerSegmentationEngine(api_key)
        self.sender = AutomatedEmailSender('gmail_credentials.json')
        self.follow_up_mgr = FollowUpManager(api_key, self.sheets, self.sender)
        
    def run_full_workflow(self):
        """Execute complete automated workflow"""
        
        print("🚀 Starting Automated Email Workflow")
        print("=" * 60)
        
        # Authenticate
        try:
            self.sheets.authenticate()
            self.sender.authenticate()
            print("✅ Authentication successful\n")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return
        
        # STEP 1: Analyze all customers
        print("\n📊 STEP 1: Customer Segmentation & Analysis")
        print("-" * 60)
        self._analyze_customers()
        
        # STEP 2: Identify follow-ups needed
        print("\n📧 STEP 2: Identify Follow-ups Needed")
        print("-" * 60)
        follow_ups = self._identify_and_queue_follow_ups()
        
        # STEP 3: Process hot leads (immediate attention)
        print("\n🔥 STEP 3: Process HOT Leads")
        print("-" * 60)
        self._process_hot_leads()
        
        # STEP 4: Send automated follow-ups (with approval)
        print("\n📤 STEP 4: Send Scheduled Follow-ups")
        print("-" * 60)
        self._send_approved_follow_ups()
        
        # STEP 5: Generate engagement report
        print("\n📈 STEP 5: Generate Daily Report")
        print("-" * 60)
        self._generate_daily_report()
        
        print("\n\n🎉 Workflow Complete!")
        print("=" * 60)
        print("📊 Check Google Sheets for:")
        print("   • Customer engagement scores")
        print("   • Pending follow-ups")
        print("   • HOT leads requiring attention")
        print("   • Daily activity report")
    
    def _analyze_customers(self):
        """Analyze all customers and segment by engagement"""
        customers = self.sheets.get_customers()
        email_history = self.sheets.get_all_emails()
        
        updates = []
        
        for customer in customers[:20]:  # Process 20 at a time
            customer_id = customer.get('id')
            customer_emails = [e for e in email_history if e.get('customer_id') == customer_id]
            
            if customer_emails:
                print(f"\n🔍 Analyzing: {customer.get('company_name')}")
                
                analysis = self.segmentation.analyze_customer_engagement(customer, customer_emails)
                
                # Update customer record
                update_data = {
                    'engagement_level': analysis.get('engagement_level'),
                    'buying_intent': analysis.get('buying_intent'),
                    'urgency_score': analysis.get('urgency_score'),
                    'next_action': analysis.get('next_action'),
                    'last_analyzed': datetime.now().strftime('%Y-%m-%d')
                }
                
                self.sheets.update_customer(customer_id, update_data)
                
                print(f"   Level: {analysis.get('engagement_level')} | Intent: {analysis.get('buying_intent')} | Urgency: {analysis.get('urgency_score')}/10")
                updates.append(update_data)
                
                time.sleep(1)  # Rate limiting
        
        print(f"\n✅ Analyzed {len(updates)} customers")
    
    def _identify_and_queue_follow_ups(self) -> List[Dict]:
        """Identify and queue follow-up emails"""
        follow_ups = self.follow_up_mgr.identify_follow_ups_needed()
        
        print(f"Found {len(follow_ups)} customers needing follow-up")
        
        for fu in follow_ups[:10]:  # Process 10 at a time
            customer = fu['customer']
            print(f"\n📨 {customer.get('company_name')} - {fu['reason']} ({fu['days_since_last']} days ago)")
            
            # Generate follow-up email
            follow_up_email = self.follow_up_mgr.generate_follow_up_email(
                customer,
                fu['last_email'],
                fu['reason']
            )
            
            if follow_up_email:
                # Log to Email_Tracking sheet for review
                email_log = {
                    'email_id': f"EMAIL_{int(time.time())}_{customer.get('id')}",
                    'customer_id': customer.get('id'),
                    'company_name': customer.get('company_name'),
                    'contact_email': customer.get('contact_email'),
                    'subject': follow_up_email['subject'],
                    'body': follow_up_email['body'],
                    'sent_date': datetime.now().strftime('%Y-%m-%d'),
                    'sent_time': '',
                    'pipeline_stage': customer.get('pipeline_stage'),
                    'email_type': 'follow_up',
                    'status': 'queued',
                    'reviewed_by': 'pending_review',
                    'follow_up_reason': fu['reason']
                }
                
                self.sheets.log_email(email_log)
                print(f"   ✅ Follow-up queued for review")
        
        return follow_ups
    
    def _process_hot_leads(self):
        """Process HOT leads requiring immediate attention"""
        customers = self.sheets.get_customers()
        hot_leads = [c for c in customers if c.get('engagement_level') == 'HOT']
        
        print(f"Found {len(hot_leads)} HOT leads")
        
        if hot_leads:
            # Create alert sheet if doesn't exist
            alert_data = []
            
            for lead in hot_leads:
                print(f"\n🔥 HOT: {lead.get('company_name')}")
                print(f"   Urgency: {lead.get('urgency_score')}/10")
                print(f"   Action: {lead.get('next_action')}")
                
                alert_data.append({
                    'customer_id': lead.get('id'),
                    'company_name': lead.get('company_name'),
                    'contact_email': lead.get('contact_email'),
                    'urgency_score': lead.get('urgency_score'),
                    'next_action': lead.get('next_action'),
                    'alert_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'needs_attention'
                })
            
            # Log to Hot_Leads sheet
            self.sheets.log_hot_leads(alert_data)
            print(f"\n✅ {len(hot_leads)} hot leads logged for immediate attention")
    
    def _send_approved_follow_ups(self):
        """Send follow-ups that have been approved"""
        approved_emails = self.sheets.get_approved_emails()
        
        print(f"Found {len(approved_emails)} approved emails to send")
        
        sent_count = 0
        for email in approved_emails[:20]:  # Max 20 per run
            success = self.sender.send_email(
                to=email.get('contact_email'),
                subject=email.get('subject'),
                body=email.get('body'),
                attachments=email.get('attachments', '').split(';') if email.get('attachments') else []
            )
            
            if success:
                # Update status in sheet
                self.sheets.update_email_status(email.get('email_id'), {
                    'status': 'sent',
                    'sent_time': datetime.now().strftime('%H:%M:%S'),
                    'reviewed_by': 'auto_sent'
                })
                sent_count += 1
                time.sleep(2)  # Rate limiting
        
        print(f"✅ Sent {sent_count} emails")
    
    def _generate_daily_report(self):
        """Generate daily activity report"""
        customers = self.sheets.get_customers()
        emails = self.sheets.get_all_emails()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Calculate metrics
        total_customers = len(customers)
        hot_leads = len([c for c in customers if c.get('engagement_level') == 'HOT'])
        warm_leads = len([c for c in customers if c.get('engagement_level') == 'WARM'])
        
        today_emails = [e for e in emails if e.get('sent_date') == today]
        emails_sent_today = len(today_emails)
        emails_replied_today = len([e for e in today_emails if e.get('replied') == 'yes'])
        
        pending_reviews = len([e for e in emails if e.get('reviewed_by') == 'pending_review'])
        
        report = {
            'date': today,
            'total_customers': total_customers,
            'hot_leads': hot_leads,
            'warm_leads': warm_leads,
            'emails_sent': emails_sent_today,
            'replies_received': emails_replied_today,
            'pending_reviews': pending_reviews,
            'response_rate': f"{(emails_replied_today/emails_sent_today*100) if emails_sent_today > 0 else 0:.1f}%"
        }
        
        print("\n📊 Today's Summary:")
        print(f"   Customers: {total_customers}")
        print(f"   HOT Leads: {hot_leads} 🔥")
        print(f"   WARM Leads: {warm_leads}")
        print(f"   Emails Sent: {emails_sent_today}")
        print(f"   Replies: {emails_replied_today}")
        print(f"   Response Rate: {report['response_rate']}")
        print(f"   Pending Reviews: {pending_reviews}")
        
        # Log report
        self.sheets.log_daily_report(report)


class GoogleSheetsManager:
    """Extended sheets manager with new methods"""
    
    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.workbook = None
        
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file('google_credentials.json', scopes=scope)
        self.client = gspread.authorize(creds)
        self.workbook = self.client.open_by_key(self.spreadsheet_id)
    
    def get_worksheet(self, sheet_name: str):
        """Get or create worksheet"""
        try:
            return self.workbook.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            return self.workbook.add_worksheet(title=sheet_name, rows=1000, cols=25)
    
    def get_customers(self) -> List[Dict]:
        """Get all customers"""
        sheet = self.get_worksheet('Customers')
        return sheet.get_all_records()
    
    def get_all_emails(self) -> List[Dict]:
        """Get all email tracking records"""
        sheet = self.get_worksheet('Email_Tracking')
        return sheet.get_all_records()
    
    def update_customer(self, customer_id: str, updates: Dict):
        """Update customer record"""
        sheet = self.get_worksheet('Customers')
        try:
            cell = sheet.find(customer_id)
            if cell:
                row = cell.row
                headers = sheet.row_values(1)
                
                for key, value in updates.items():
                    if key in headers:
                        col = headers.index(key) + 1
                        sheet.update_cell(row, col, str(value))
        except:
            pass
    
    def log_email(self, email_data: Dict):
        """Log email to tracking sheet"""
        sheet = self.get_worksheet('Email_Tracking')
        headers = sheet.row_values(1)
        
        if not headers:
            headers = list(email_data.keys())
            sheet.append_row(headers)
        
        row = [str(email_data.get(h, '')) for h in headers]
        sheet.append_row(row)
    
    def get_approved_emails(self) -> List[Dict]:
        """Get emails approved for sending"""
        sheet = self.get_worksheet('Email_Tracking')
        records = sheet.get_all_records()
        return [r for r in records if r.get('reviewed_by') == 'approved' and r.get('status') == 'queued']
    
    def update_email_status(self, email_id: str, updates: Dict):
        """Update email status"""
        sheet = self.get_worksheet('Email_Tracking')
        try:
            cell = sheet.find(email_id)
            if cell:
                row = cell.row
                headers = sheet.row_values(1)
                
                for key, value in updates.items():
                    if key in headers:
                        col = headers.index(key) + 1
                        sheet.update_cell(row, col, str(value))
        except:
            pass
    
    def log_hot_leads(self, alerts: List[Dict]):
        """Log hot leads requiring attention"""
        sheet = self.get_worksheet('Hot_Leads_Alert')
        headers = sheet.row_values(1)
        
        if not headers and alerts:
            headers = list(alerts[0].keys())
            sheet.append_row(headers)
        
        for alert in alerts:
            row = [str(alert.get(h, '')) for h in headers]
            sheet.append_row(row)
    
    def log_daily_report(self, report: Dict):
        """Log daily report"""
        sheet = self.get_worksheet('Daily_Reports')
        headers = sheet.row_values(1)
        
        if not headers:
            headers = list(report.keys())
            sheet.append_row(headers)
        
        row = [str(report.get(h, '')) for h in headers]
        sheet.append_row(row)


def main():
    """Main execution"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('config/.env')
    
    SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
    API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    if not SHEETS_ID or not API_KEY:
        print("❌ Missing configuration. Check config/.env file")
        return
    
    # Run workflow
    orchestrator = SmartWorkflowOrchestrator(SHEETS_ID, API_KEY)
    orchestrator.run_full_workflow()


if __name__ == "__main__":
    main()
