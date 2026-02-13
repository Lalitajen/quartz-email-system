"""
Quartz Email Outreach System - Main Script
Handles AI Research, Email Tracking, and Auto-Reply Generation
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import anthropic
import requests
from bs4 import BeautifulSoup

# Configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
GOOGLE_SHEETS_ID = os.environ.get('GOOGLE_SHEETS_ID', '')
GMAIL_CREDENTIALS_PATH = os.environ.get('GMAIL_CREDENTIALS_PATH', 'gmail_credentials.json')

# Pipeline stage configurations
PIPELINE_STAGES = {
    1: {
        "name": "Prospecting",
        "attachments": ["01_Brochure.pdf"],
        "trigger_keywords": ["cold outreach", "introduction", "first contact"],
        "followup_days": 5
    },
    2: {
        "name": "Initial Contact",
        "attachments": ["01_Brochure.pdf", "02_Technical_Data_Sheet.pdf"],
        "trigger_keywords": ["interested", "more info", "specifications"],
        "followup_days": 4
    },
    3: {
        "name": "Qualification",
        "attachments": ["02_Technical_Data_Sheet.pdf", "04_Detailed_Brochure.pdf"],
        "trigger_keywords": ["purity", "SiO2", "boron", "specifications", "ICP-MS"],
        "followup_days": 3
    },
    4: {
        "name": "Sample & Testing",
        "attachments": ["02_Technical_Data_Sheet.pdf", "Sample_Request_Form.pdf"],
        "trigger_keywords": ["sample", "trial", "test", "2-5kg", "lab"],
        "followup_days": 5
    },
    5: {
        "name": "Negotiation",
        "attachments": ["03_Quotation.pdf"],
        "trigger_keywords": ["price", "quote", "quotation", "cost", "FOB", "CIF", "volume"],
        "followup_days": 2
    },
    6: {
        "name": "Contract",
        "attachments": ["Contract_Template.pdf", "03_Quotation.pdf"],
        "trigger_keywords": ["contract", "agreement", "terms", "payment"],
        "followup_days": 3
    },
    7: {
        "name": "Fulfillment",
        "attachments": ["COA.pdf", "Shipping_Docs.pdf"],
        "trigger_keywords": ["delivery", "shipping", "invoice", "COA"],
        "followup_days": 3
    },
    8: {
        "name": "Follow-Up & Satisfaction",
        "attachments": ["Customer_Satisfaction_Survey.pdf"],
        "trigger_keywords": ["feedback", "satisfied", "review", "quality", "reorder", "experience"],
        "followup_days": 7
    },
    9: {
        "name": "Repeat Customer",
        "attachments": ["VIP_Discount_Program.pdf", "Bulk_Order_Benefits.pdf"],
        "trigger_keywords": ["repeat", "again", "more", "container", "bulk", "regular order"],
        "followup_days": 7
    },
    10: {
        "name": "Lost/Inactive",
        "attachments": [],
        "trigger_keywords": ["not interested", "pass", "decline", "later", "no thanks", "unsubscribe"],
        "followup_days": 0
    }
}


class GoogleSheetsManager:
    """Manages interactions with Google Sheets"""
    
    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.sheets = {}
        
    def authenticate(self):
        """Authenticate with Google Sheets API using service account file."""
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        sa_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'service_account.json')
        creds = Credentials.from_service_account_file(sa_path, scopes=scope)
        self.client = gspread.authorize(creds)
        self.workbook = self.client.open_by_key(self.spreadsheet_id)

    def authenticate_from_json(self, service_account_json: str):
        """Authenticate using service account JSON string (from database)."""
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        sa_info = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
        creds = Credentials.from_service_account_info(sa_info, scopes=scope)
        self.client = gspread.authorize(creds)
        self.workbook = self.client.open_by_key(self.spreadsheet_id)
        
    def get_worksheet(self, sheet_name: str):
        """Get or create worksheet"""
        try:
            return self.workbook.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            return self.workbook.add_worksheet(title=sheet_name, rows=1000, cols=20)
    
    def get_customers(self, status: Optional[str] = None) -> List[Dict]:
        """Get customer list from sheet"""
        sheet = self.get_worksheet('Customers')
        records = sheet.get_all_records()
        
        if status:
            return [r for r in records if r.get('research_status') == status]
        return records
    
    def update_customer(self, customer_id: str, updates: Dict):
        """Update customer record"""
        sheet = self.get_worksheet('Customers')
        cell = sheet.find(customer_id)
        
        if cell:
            row = cell.row
            headers = sheet.row_values(1)
            
            for key, value in updates.items():
                if key in headers:
                    col = headers.index(key) + 1
                    sheet.update_cell(row, col, value)
    
    def log_email(self, email_data: Dict):
        """Log sent email to tracking sheet"""
        sheet = self.get_worksheet('Email_Tracking')
        
        # Get headers
        headers = sheet.row_values(1)
        if not headers:
            headers = list(email_data.keys())
            sheet.append_row(headers)
        
        # Append email log
        row = [email_data.get(h, '') for h in headers]
        sheet.append_row(row)
    
    def get_pending_reviews(self) -> List[Dict]:
        """Get emails pending human review"""
        sheet = self.get_worksheet('Email_Tracking')
        records = sheet.get_all_records()
        return [r for r in records if r.get('reviewed_by') == 'pending_review']


class AIResearchEngine:
    """AI-powered customer research"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        
    def research_company(self, company_name: str, website: str) -> Dict:
        """Perform AI research on a company"""
        print(f"🔍 Researching: {company_name}")
        
        # Step 1: Scrape website
        website_content = self._scrape_website(website)
        
        # Step 2: AI Analysis
        research_data = self._analyze_with_ai(company_name, website_content)
        
        return research_data
    
    @staticmethod
    def _is_safe_url(url: str) -> bool:
        """Validate URL to prevent SSRF attacks (A10)."""
        from urllib.parse import urlparse
        import ipaddress
        import socket

        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False
            hostname = parsed.hostname
            if not hostname:
                return False
            blocked_hosts = {'localhost', '127.0.0.1', '::1', '0.0.0.0',
                             'metadata.google.internal', 'metadata'}
            if hostname.lower() in blocked_hosts:
                return False
            try:
                addr = socket.getaddrinfo(hostname, None)[0][4][0]
                ip = ipaddress.ip_address(addr)
                if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
                    return False
            except (socket.gaierror, ValueError):
                return False
            return True
        except Exception:
            return False

    def _scrape_website(self, url: str) -> str:
        """Scrape company website with SSRF protection."""
        try:
            if not self._is_safe_url(url):
                print(f"URL blocked by security policy: {url}")
                return ""
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; QuartzBot/1.0)'}
            response = requests.get(url, headers=headers, timeout=10,
                                    allow_redirects=False)
            if response.is_redirect:
                redirect_url = response.headers.get('Location', '')
                if not self._is_safe_url(redirect_url):
                    return ""
                response = requests.get(redirect_url, headers=headers, timeout=10,
                                        allow_redirects=False)
            if len(response.content) > 1_000_000:
                return ""
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract text from main content areas
            text = ' '.join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3'])])
            return text[:5000]  # Limit to first 5000 chars

        except Exception as e:
            print(f"Website scraping failed: {e}")
            return ""
    
    def _analyze_with_ai(self, company_name: str, website_content: str) -> Dict:
        """Use Claude to analyze company and generate insights"""
        
        prompt = f"""Analyze this company for B2B outreach in the high-purity quartz mining industry.

Company: {company_name}
Website Content: {website_content}

Please provide:
1. Company summary (2-3 sentences)
2. Industry and products
3. Potential pain points related to quartz/mineral materials
4. Suggested outreach approach
5. Estimated company size (Small/Medium/Large)

Format as JSON with keys: summary, industry, pain_points, outreach_approach, company_size"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Try to extract JSON from response
            if '{' in response_text and '}' in response_text:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                research_data = json.loads(response_text[json_start:json_end])
            else:
                research_data = {
                    "summary": response_text[:200],
                    "industry": "Unknown",
                    "pain_points": "Requires manual review",
                    "outreach_approach": "Standard introduction",
                    "company_size": "Unknown"
                }
            
            return research_data
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            return {
                "summary": "Research failed - manual review needed",
                "industry": "Unknown",
                "pain_points": "",
                "outreach_approach": "Standard approach",
                "company_size": "Unknown"
            }


class EmailPersonalizationEngine:
    """Generate personalized emails with AI"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.sender_name = os.getenv('SENDER_NAME', 'Sales Team')
        self.sender_title = os.getenv('SENDER_TITLE', '')
        self.company_name = os.getenv('COMPANY_NAME', 'Lorh La Seng Commercial')
        self.company_phone = os.getenv('COMPANY_PHONE', '')
        self.company_website = os.getenv('COMPANY_WEBSITE', '')
        self.company_address = os.getenv('COMPANY_ADDRESS', '')

    def _build_signature(self) -> str:
        """Build email signature from company details"""
        sig = f"Best regards,\n\n{self.sender_name}"
        if self.sender_title:
            sig += f"\n{self.sender_title}"
        sig += f"\n{self.company_name}"
        if self.company_phone:
            sig += f"\nPhone: {self.company_phone}"
        if self.company_website:
            sig += f"\nWebsite: {self.company_website}"
        if self.company_address:
            sig += f"\n{self.company_address}"
        return sig

    def generate_email(self, customer: Dict, research: Dict, stage: int, context: str = "") -> Dict:
        """Generate personalized email based on customer data and pipeline stage"""

        stage_name = PIPELINE_STAGES[stage]["name"]
        signature = self._build_signature()

        prompt = f"""Generate a professional B2B sales email for a high-purity quartz export company.

Customer Details:
- Company: {customer.get('company_name')}
- Contact: {customer.get('contact_name')}
- Industry: {research.get('industry', 'Manufacturing')}
- Pain Points: {research.get('pain_points', 'Need reliable quartz supplier')}

Pipeline Stage: {stage_name} (Stage {stage})
Company Research: {research.get('summary', '')}
Additional Context: {context}

Sender Information:
- Name: {self.sender_name}
- Title: {self.sender_title}
- Company: {self.company_name}

Email Requirements:
1. Professional B2B tone
2. Personalized to their industry and pain points
3. Clear value proposition for high-purity quartz
4. Appropriate for {stage_name} stage
5. Include relevant call-to-action
6. Keep it concise (150-250 words)
7. End the email body with this EXACT signature:

{signature}

Generate:
- Subject line
- Email body (MUST end with the signature above)
- Suggested attachments (from: {', '.join(PIPELINE_STAGES[stage]['attachments'])})

Format as JSON with keys: subject, body, attachments, confidence_score"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Extract JSON
            if '{' in response_text and '}' in response_text:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                email_data = json.loads(response_text[json_start:json_end])
            else:
                email_data = {
                    "subject": f"High-Purity Quartz Solutions for {customer.get('company_name')}",
                    "body": response_text,
                    "attachments": PIPELINE_STAGES[stage]["attachments"],
                    "confidence_score": 0.5
                }
            
            return email_data
            
        except Exception as e:
            print(f"⚠️ Email generation failed: {e}")
            return None


class EmailTracker:
    """Monitor and track email responses"""
    
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self.service = None
        
    def authenticate(self):
        """Authenticate with Gmail API"""
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
                  'https://www.googleapis.com/auth/gmail.send']
        
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def check_new_replies(self, since_hours: int = 24) -> List[Dict]:
        """Check for new customer replies"""
        if not self.service:
            self.authenticate()
        
        # Calculate time threshold
        time_threshold = datetime.now() - timedelta(hours=since_hours)
        query = f'is:unread after:{time_threshold.strftime("%Y/%m/%d")}'
        
        try:
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            replies = []
            for msg in messages:
                msg_data = self.service.users().messages().get(userId='me', id=msg['id']).execute()
                
                # Extract email details
                headers = msg_data['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
                
                # Get email body
                body = self._get_email_body(msg_data)
                
                replies.append({
                    'message_id': msg['id'],
                    'subject': subject,
                    'from': sender,
                    'body': body,
                    'date': msg_data['internalDate']
                })
            
            return replies
            
        except Exception as e:
            print(f"⚠️ Error checking emails: {e}")
            return []
    
    def _get_email_body(self, msg_data: Dict) -> str:
        """Extract email body from message"""
        try:
            if 'parts' in msg_data['payload']:
                parts = msg_data['payload']['parts']
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        import base64
                        data = part['body']['data']
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                import base64
                data = msg_data['payload']['body']['data']
                return base64.urlsafe_b64decode(data).decode('utf-8')
        except:
            return ""


class AutoReplyEngine:
    """Generate automatic reply suggestions"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.email_engine = EmailPersonalizationEngine(api_key)
    
    def analyze_and_generate_reply(self, customer: Dict, reply_email: Dict) -> Dict:
        """Analyze customer reply and generate response"""
        
        prompt = f"""Analyze this customer email reply and suggest appropriate response for a quartz export company.

Customer: {customer.get('company_name')}
Current Pipeline Stage: {customer.get('pipeline_stage')}

Customer's Email:
Subject: {reply_email['subject']}
Body: {reply_email['body']}

Analysis needed:
1. Intent (request_info, request_sample, request_quote, question, objection, other)
2. Urgency (high, medium, low)
3. Suggested next pipeline stage
4. Key points to address in response
5. Recommended attachments

Format as JSON with keys: intent, urgency, next_stage, key_points, attachments, confidence"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Extract analysis
            if '{' in response_text and '}' in response_text:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                analysis = json.loads(response_text[json_start:json_end])
            else:
                analysis = {
                    "intent": "question",
                    "urgency": "medium",
                    "next_stage": customer.get('pipeline_stage', 1),
                    "key_points": ["Address customer inquiry"],
                    "attachments": [],
                    "confidence": 0.5
                }
            
            # Generate response email
            context = f"Customer replied with: {reply_email['body'][:200]}. Intent: {analysis['intent']}"
            next_stage = analysis.get('next_stage', customer.get('pipeline_stage', 1))
            
            reply_draft = self.email_engine.generate_email(customer, {}, next_stage, context)
            
            return {
                "analysis": analysis,
                "draft_reply": reply_draft,
                "suggested_stage": next_stage
            }
            
        except Exception as e:
            print(f"⚠️ Reply generation failed: {e}")
            return None


def main_workflow():
    """Main automation workflow"""
    
    print("🚀 Quartz Email Outreach System Starting...")
    
    # Initialize components
    sheets = GoogleSheetsManager(GOOGLE_SHEETS_ID)
    research_engine = AIResearchEngine(ANTHROPIC_API_KEY)
    email_engine = EmailPersonalizationEngine(ANTHROPIC_API_KEY)
    tracker = EmailTracker(GMAIL_CREDENTIALS_PATH)
    auto_reply = AutoReplyEngine(ANTHROPIC_API_KEY)
    
    try:
        sheets.authenticate()
        print("✅ Connected to Google Sheets")
    except Exception as e:
        print(f"❌ Google Sheets connection failed: {e}")
        return
    
    # PHASE 1: Research pending customers
    print("\n📊 PHASE 1: AI Research")
    pending_research = sheets.get_customers(status='pending')
    
    for customer in pending_research[:5]:  # Process 5 at a time
        print(f"\n🔍 Researching: {customer['company_name']}")
        
        research = research_engine.research_company(
            customer['company_name'],
            customer.get('company_website', '')
        )
        
        # Update sheet with research
        sheets.update_customer(customer['id'], {
            'research_status': 'completed',
            'research_summary': research.get('summary', ''),
            'pain_points': research.get('pain_points', '')
        })
        
        print(f"✅ Research completed for {customer['company_name']}")
        time.sleep(2)  # Rate limiting
    
    # PHASE 2: Check for new email replies
    print("\n📧 PHASE 2: Email Tracking")
    new_replies = tracker.check_new_replies(since_hours=24)
    
    print(f"Found {len(new_replies)} new replies")
    
    for reply in new_replies:
        sender_email = reply['from']
        
        # Find customer in database
        customers = sheets.get_customers()
        customer = next((c for c in customers if sender_email in c.get('contact_email', '')), None)
        
        if customer:
            print(f"\n💬 Processing reply from: {customer['company_name']}")
            
            # Generate auto-reply
            response = auto_reply.analyze_and_generate_reply(customer, reply)
            
            if response:
                # Log for human review
                email_log = {
                    'email_id': f"EMAIL{int(time.time())}",
                    'customer_id': customer['id'],
                    'company_name': customer['company_name'],
                    'contact_email': customer['contact_email'],
                    'subject': response['draft_reply']['subject'],
                    'sent_date': datetime.now().strftime('%Y-%m-%d'),
                    'sent_time': datetime.now().strftime('%H:%M:%S'),
                    'pipeline_stage': response['suggested_stage'],
                    'email_type': 'auto_reply',
                    'attachments': ';'.join(response['draft_reply'].get('attachments', [])),
                    'status': 'draft',
                    'ai_confidence': response['draft_reply'].get('confidence_score', 0.5),
                    'reviewed_by': 'pending_review',
                    'reply_content_summary': response['analysis']['intent']
                }
                
                sheets.log_email(email_log)
                print(f"✅ Auto-reply drafted and queued for review")
    
    print("\n\n🎉 Workflow completed!")
    print("📋 Check Google Sheets for:")
    print("   - Updated customer research")
    print("   - Draft emails pending your review")


if __name__ == "__main__":
    main_workflow()
