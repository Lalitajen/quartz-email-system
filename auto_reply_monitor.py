#!/usr/bin/env python3 -u
"""
Automated Reply Monitor - Runs every N hours
Checks Gmail for replies, detects customer requests by pipeline stage keywords,
updates Email Tracking, and flags stale emails for follow-up.
Logs all activity to logs/auto_reply.log for web UI monitoring.
"""
import os
import sys
import time
import json
import logging
import schedule
from datetime import datetime, timedelta
from pathlib import Path

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

# Add scripts directory to path
sys.path.append('scripts')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('config/.env')

from main_automation import EmailTracker, GoogleSheetsManager, EmailPersonalizationEngine, PIPELINE_STAGES
from app_core import classify_reply

# Configuration
CHECK_INTERVAL_HOURS = int(os.getenv('EMAIL_CHECK_INTERVAL_HOURS', '24'))
FOLLOWUP_DAYS = int(os.getenv('FOLLOWUP_DAYS', '3'))
SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
SENDER_NAME = os.getenv('SENDER_NAME', '')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')

# Setup file logging
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'auto_reply.log'
ACTIVITY_FILE = LOG_DIR / 'auto_reply_activity.json'

# Configure logger
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(message)s'))

monitor_logger = logging.getLogger('auto_reply_monitor')
monitor_logger.setLevel(logging.INFO)
monitor_logger.addHandler(file_handler)
monitor_logger.addHandler(console_handler)


def log_activity(action, details):
    """Append activity entry to JSON log for web UI."""
    entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': action,
        **details
    }
    try:
        activities = []
        if ACTIVITY_FILE.exists():
            with open(ACTIVITY_FILE, 'r') as f:
                activities = json.load(f)
        activities.append(entry)
        # Keep last 200 entries
        activities = activities[-200:]
        with open(ACTIVITY_FILE, 'w') as f:
            json.dump(activities, f, indent=2)
    except Exception:
        pass


def detect_pipeline_stage(reply_body, reply_subject, current_stage=1):
    """Detect which pipeline stage a customer request matches based on keywords"""
    text = (reply_body + ' ' + reply_subject).lower()

    matched_stage = None
    max_matches = 0

    for stage_num in sorted(PIPELINE_STAGES.keys(), reverse=True):
        stage = PIPELINE_STAGES[stage_num]
        keywords = stage.get('trigger_keywords', [])
        matches = sum(1 for kw in keywords if kw.lower() in text)

        if matches > max_matches:
            max_matches = matches
            matched_stage = stage_num

    if matched_stage and max_matches > 0:
        return matched_stage

    next_stage = min(current_stage + 1, max(PIPELINE_STAGES.keys()))
    return next_stage


def classify_request(reply_body):
    """Classify the type of customer request. Wraps shared classify_reply."""
    req_type, _ = classify_reply(reply_body)
    return req_type


class AutoReplyMonitor:
    """Automatically monitor and process email replies"""

    def __init__(self):
        self.tracker = None
        self.sheets = None
        self.last_check = None
        self.stats = {'checks': 0, 'replies_found': 0, 'updated': 0, 'stale_found': 0, 'errors': 0}

    def initialize(self):
        """Initialize connections"""
        monitor_logger.info("Initializing Auto Reply Monitor...")

        self.tracker = EmailTracker('gmail_credentials.json')
        self.tracker.authenticate()
        monitor_logger.info("Gmail authenticated")

        self.sheets = GoogleSheetsManager(SHEETS_ID)
        self.sheets.authenticate()
        monitor_logger.info("Google Sheets connected")

        # Write PID file for web UI status detection
        pid_file = LOG_DIR / 'auto_reply.pid'
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))

        log_activity('daemon_start', {
            'pid': os.getpid(),
            'interval_hours': CHECK_INTERVAL_HOURS,
            'email': SENDER_EMAIL,
        })

    def check_and_update_replies(self):
        """Check for new replies and update tracking with stage detection"""
        self.stats['checks'] += 1
        monitor_logger.info(f"{'='*60}")
        monitor_logger.info(f"Checking for replies...")

        try:
            replies = self.tracker.check_new_replies(since_hours=CHECK_INTERVAL_HOURS)

            if not replies:
                monitor_logger.info("No new replies found")
                log_activity('check_replies', {'found': 0, 'updated': 0})
                self.last_check = datetime.now()
                return

            monitor_logger.info(f"Found {len(replies)} reply(ies)")
            self.stats['replies_found'] += len(replies)

            tracking_sheet = self.sheets.get_worksheet('Email_Tracking')
            tracking_records = tracking_sheet.get_all_records()
            headers = tracking_sheet.row_values(1)

            for col_name in ['replied', 'reply_date', 'reply_content_summary', 'next_action', 'detected_stage']:
                if col_name not in headers:
                    tracking_sheet.update_cell(1, len(headers) + 1, col_name)
                    headers.append(col_name)

            customers_sheet = self.sheets.get_worksheet('Customers')
            customers = customers_sheet.get_all_records()
            customer_headers = customers_sheet.row_values(1)

            updated_count = 0
            known_spam = ['@accounts.google.com', '@indeed.com', '@pinterest.com',
                          '@discover.pinterest.com', '@email.shopify.com',
                          '@englishgrammar.org', '@360alumni.com']

            for reply in replies:
                from_email = reply['from']
                if '<' in from_email:
                    from_email = from_email.split('<')[1].split('>')[0].strip()

                if any(domain in from_email for domain in known_spam):
                    continue

                monitor_logger.info(f"Processing reply from: {from_email}")
                reply_body = reply.get('body', '')
                request_type = classify_request(reply_body)
                monitor_logger.info(f"  Request Type: {request_type}")

                for idx, record in enumerate(tracking_records, start=2):
                    if record.get('contact_email') == from_email and record.get('status') in ['sent', 'queued']:
                        current_stage = int(record.get('pipeline_stage', 1)) if str(record.get('pipeline_stage', '1')).isdigit() else 1
                        detected_stage = detect_pipeline_stage(reply_body, reply['subject'], current_stage)
                        stage_info = PIPELINE_STAGES.get(detected_stage, {})
                        stage_name = stage_info.get('name', '')
                        attachments = stage_info.get('attachments', [])

                        monitor_logger.info(f"  Stage: {current_stage} -> {detected_stage} ({stage_name})")

                        if request_type == 'Declined':
                            next_action = 'Customer declined - move to Lost/Inactive'
                        else:
                            next_action = f"Send Stage {detected_stage} ({stage_name}) with {', '.join(attachments)}" if attachments else f"Follow up - Stage {detected_stage}"

                        updates = {
                            'status': 'replied',
                            'replied': 'yes',
                            'reply_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'reply_content_summary': f"[{request_type}] {reply_body[:150]}",
                            'next_action': next_action,
                            'detected_stage': str(detected_stage)
                        }

                        for col_name, value in updates.items():
                            if col_name in headers:
                                tracking_sheet.update_cell(idx, headers.index(col_name) + 1, value)

                        updated_count += 1
                        self.stats['updated'] += 1

                        log_activity('reply_processed', {
                            'from': from_email,
                            'request_type': request_type,
                            'current_stage': current_stage,
                            'detected_stage': detected_stage,
                            'stage_name': stage_name,
                            'email_id': record.get('email_id', ''),
                            'company': record.get('company_name', ''),
                            'result': 'updated',
                        })

                        customer_id = record.get('customer_id')
                        if customer_id:
                            self.update_customer(customer_id, from_email, detected_stage, request_type,
                                                 customers_sheet, customer_headers, customers)
                        break

            monitor_logger.info(f"Updated {updated_count} email tracking record(s)")
            log_activity('check_replies', {'found': len(replies), 'updated': updated_count})
            self.last_check = datetime.now()

        except Exception as e:
            self.stats['errors'] += 1
            monitor_logger.error(f"Error checking replies: {e}")
            log_activity('error', {'action': 'check_replies', 'error': str(e)})
            import traceback
            traceback.print_exc()

    def update_customer(self, customer_id, email, new_stage, request_type, sheet, headers, customers):
        """Update customer engagement level and pipeline stage"""
        try:
            for idx, customer in enumerate(customers, start=2):
                if str(customer.get('id')) == str(customer_id) or customer.get('contact_email') == email:
                    engagement_map = {
                        'Quotation Request': 'HOT',
                        'Sample Request': 'HOT',
                        'Contract Request': 'HOT',
                        'Technical Info Request': 'WARM',
                        'Info Request': 'INTERESTED',
                        'Shipping Inquiry': 'HOT',
                        'Repeat Order': 'HOT',
                        'Declined': 'COLD',
                        'General Reply': 'INTERESTED'
                    }
                    new_engagement = engagement_map.get(request_type, 'INTERESTED')

                    if 'engagement_level' in headers:
                        col = headers.index('engagement_level') + 1
                        sheet.update_cell(idx, col, new_engagement)

                    if 'pipeline_stage' in headers:
                        col = headers.index('pipeline_stage') + 1
                        sheet.update_cell(idx, col, new_stage)

                    monitor_logger.info(f"  Customer updated: engagement={new_engagement}, stage={new_stage}")
                    break
        except Exception as e:
            monitor_logger.warning(f"Could not update customer: {e}")

    def check_stale_followups(self):
        """Find sent emails past their per-stage follow-up delay with no reply."""
        monitor_logger.info(f"{'='*60}")
        monitor_logger.info("Checking for stale emails needing follow-up...")

        try:
            tracking_sheet = self.sheets.get_worksheet('Email_Tracking')
            emails = tracking_sheet.get_all_records()
            headers = tracking_sheet.row_values(1)

            now = datetime.now()
            stale_count = 0

            for idx, e in enumerate(emails, start=2):
                if e.get('status') != 'sent' or e.get('replied', 'no') == 'yes':
                    continue

                sent_date_str = e.get('sent_date', '')
                if not sent_date_str:
                    continue
                try:
                    sent_date = datetime.strptime(sent_date_str, '%Y-%m-%d')
                except ValueError:
                    continue

                current_stage = int(e.get('pipeline_stage', 1)) if str(e.get('pipeline_stage', '1')).isdigit() else 1
                delay_days = PIPELINE_STAGES.get(current_stage, {}).get('followup_days', FOLLOWUP_DAYS)

                if delay_days == 0:
                    continue

                if (now - sent_date).days >= delay_days:
                    next_stage = min(current_stage + 1, max(PIPELINE_STAGES.keys()))
                    stage_info = PIPELINE_STAGES.get(next_stage, {})

                    next_action = f'Follow-up needed: Stage {next_stage} ({stage_info.get("name", "")}) - {delay_days}d delay exceeded'
                    if 'next_action' in headers:
                        tracking_sheet.update_cell(idx, headers.index('next_action') + 1, next_action)

                    monitor_logger.info(f"  Stale: {e.get('company_name', '')} - sent {sent_date_str}, "
                                        f"stage {current_stage} ({delay_days}d delay) -> needs Stage {next_stage}")
                    stale_count += 1

            self.stats['stale_found'] += stale_count
            monitor_logger.info(f"Found {stale_count} email(s) needing follow-up")
            log_activity('check_stale', {'stale_count': stale_count})

        except Exception as e:
            self.stats['errors'] += 1
            monitor_logger.error(f"Error checking stale emails: {e}")
            log_activity('error', {'action': 'check_stale', 'error': str(e)})
            import traceback
            traceback.print_exc()

    def run(self):
        """Run the monitoring service"""
        monitor_logger.info("=" * 60)
        monitor_logger.info("  Auto Reply Monitor Service")
        monitor_logger.info("=" * 60)
        monitor_logger.info(f"  Check Interval: Every {CHECK_INTERVAL_HOURS} hour(s)")
        monitor_logger.info(f"  Gmail: {SENDER_EMAIL}")
        monitor_logger.info(f"  Pipeline Stages: {len(PIPELINE_STAGES)}")
        monitor_logger.info(f"  Log File: {LOG_FILE}")
        monitor_logger.info(f"  Activity Log: {ACTIVITY_FILE}")
        monitor_logger.info("=" * 60)

        self.initialize()

        monitor_logger.info("Running initial check...")
        self.check_and_update_replies()
        self.check_stale_followups()

        schedule.every(CHECK_INTERVAL_HOURS).hours.do(self.check_and_update_replies)
        schedule.every(CHECK_INTERVAL_HOURS).hours.do(self.check_stale_followups)

        monitor_logger.info(f"Scheduled to run every {CHECK_INTERVAL_HOURS} hour(s)")
        monitor_logger.info("Press Ctrl+C to stop")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            monitor_logger.info("Auto Reply Monitor stopped")
            log_activity('daemon_stop', {'pid': os.getpid()})
            # Clean up PID file
            pid_file = LOG_DIR / 'auto_reply.pid'
            if pid_file.exists():
                pid_file.unlink()


if __name__ == "__main__":
    monitor = AutoReplyMonitor()
    monitor.run()
