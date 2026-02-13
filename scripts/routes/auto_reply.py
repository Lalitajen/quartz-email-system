"""Auto-reply monitoring route with daemon controls and reply inbox."""

import os
import signal
import subprocess
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from app_core import (login_required, PIPELINE_STAGES, get_sheets, get_user_config,
                      SPAM_DOMAINS, classify_reply, logger,
                      safe_flash_error, get_gmail_service_for_user, EmailTracker)

auto_reply_bp = Blueprint('auto_reply', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@auto_reply_bp.route('/auto-reply')
@login_required
def auto_reply_page():
    followup_days = get_user_config('followup_days', 3)

    daemon_status = {'running': False, 'pid': None, 'status': 'STOPPED'}
    statistics = {}
    recent_activity = []
    stage_dist = {}
    log_lines = []
    available = False

    try:
        from daemon_integration import (
            get_daemon_status, get_daemon_statistics,
            get_recent_activity, get_stage_distribution,
            get_log_tail
        )
        daemon_status = get_daemon_status()
        statistics = get_daemon_statistics()
        recent_activity = get_recent_activity(limit=20)
        stage_dist = get_stage_distribution()
        log_lines = get_log_tail(lines=40)
        available = True
    except ImportError:
        logger.warning("daemon_integration module not available")
    except Exception as e:
        logger.error(f"Auto-reply page error: {e}")

    reply_inbox = []
    reply_stats = {'total_replies': 0, 'needs_action': 0, 'hot_leads': 0, 'declined': 0}
    try:
        sheets = get_sheets()
        tracking_sheet = sheets.get_worksheet('Email_Tracking')
        emails = tracking_sheet.get_all_records()
        customers = sheets.get_customers()
        customer_map = {str(c.get('id', '')): c for c in customers}

        for e in emails:
            if e.get('replied') != 'yes':
                continue
            reply_stats['total_replies'] += 1

            reply_summary = str(e.get('reply_content_summary', ''))
            req_type = ''
            if reply_summary.startswith('[') and ']' in reply_summary:
                req_type = reply_summary[1:reply_summary.index(']')]

            if req_type in ('Quotation Request', 'Sample Request', 'Contract Request', 'Repeat Order'):
                reply_stats['hot_leads'] += 1
            elif req_type == 'Declined':
                reply_stats['declined'] += 1

            status = e.get('status', '')
            if status == 'replied':
                reply_stats['needs_action'] += 1
                customer = customer_map.get(str(e.get('customer_id', '')), {})
                detected = str(e.get('detected_stage', ''))
                detected_info = PIPELINE_STAGES.get(int(detected), {}) if detected.isdigit() else {}

                reply_inbox.append({
                    'email_id': e.get('email_id', ''),
                    'customer_id': e.get('customer_id', ''),
                    'company_name': e.get('company_name', customer.get('company_name', '-')),
                    'contact_email': e.get('contact_email', ''),
                    'subject': e.get('subject', ''),
                    'reply_date': e.get('reply_date', ''),
                    'request_type': req_type,
                    'reply_summary': reply_summary,
                    'detected_stage': detected,
                    'detected_stage_name': detected_info.get('name', ''),
                    'detected_attachments': detected_info.get('attachments', []),
                    'status': status,
                    'engagement': customer.get('engagement_level', ''),
                })

        reply_inbox.sort(key=lambda x: x.get('reply_date', ''), reverse=True)

    except Exception as e:
        logger.error(f"Reply inbox load error: {e}")

    email_summary = {'total': 0, 'sent': 0, 'queued': 0, 'stale': 0}
    try:
        now = datetime.now()
        for e in emails:
            email_summary['total'] += 1
            st = e.get('status', '')
            if st == 'sent':
                email_summary['sent'] += 1
                sent_date_str = e.get('sent_date', '')
                if sent_date_str and e.get('replied', 'no') != 'yes':
                    try:
                        sent_date = datetime.strptime(sent_date_str, '%Y-%m-%d')
                        current_stage = int(e.get('pipeline_stage', 1)) if str(e.get('pipeline_stage', '1')).isdigit() else 1
                        delay = PIPELINE_STAGES.get(current_stage, {}).get('followup_days', followup_days)
                        if delay > 0 and (now - sent_date).days >= delay:
                            email_summary['stale'] += 1
                    except ValueError:
                        pass
            elif st == 'queued':
                email_summary['queued'] += 1
    except Exception:
        pass

    return render_template('auto_reply.html',
        active_page='auto_reply',
        available=available,
        daemon_status=daemon_status,
        statistics=statistics,
        recent_activity=recent_activity,
        stage_dist=stage_dist,
        log_lines=log_lines,
        pipeline_stages=PIPELINE_STAGES,
        reply_inbox=reply_inbox,
        reply_stats=reply_stats,
        email_summary=email_summary,
    )


@auto_reply_bp.route('/auto-reply/check-now')
@login_required
def check_replies_now():
    """Manually trigger a reply check."""
    try:
        gmail_service = get_gmail_service_for_user()
        tracker = EmailTracker.__new__(EmailTracker)
        tracker.service = gmail_service

        replies = tracker.check_new_replies(since_hours=48)

        if not replies:
            flash('No new replies found in the last 48 hours.', 'info')
            return redirect(url_for('auto_reply.auto_reply_page'))

        sheets = get_sheets()
        tracking_sheet = sheets.get_worksheet('Email_Tracking')
        tracking_records = tracking_sheet.get_all_records()
        headers = tracking_sheet.row_values(1)

        for col_name in ['replied', 'reply_date', 'reply_content_summary', 'next_action', 'detected_stage']:
            if col_name not in headers:
                tracking_sheet.update_cell(1, len(headers) + 1, col_name)
                headers.append(col_name)

        updated = 0
        for reply in replies:
            from_email = reply['from']
            if '<' in from_email:
                from_email = from_email.split('<')[1].split('>')[0].strip()

            if any(d in from_email.lower() for d in SPAM_DOMAINS):
                continue

            reply_body = reply.get('body', '')
            req_type, detected_stage = classify_reply(reply_body)

            import time as time_mod
            for idx, record in enumerate(tracking_records, start=2):
                record_email = record.get('contact_email', '').lower()
                if record_email and record_email == from_email.lower():
                    current_stage = int(record.get('pipeline_stage', 1)) if str(record.get('pipeline_stage', '')).isdigit() else 1
                    if detected_stage is None:
                        detected_stage = min(current_stage + 1, max(PIPELINE_STAGES.keys()))

                    updates = {
                        'replied': 'yes',
                        'reply_date': datetime.now().strftime('%Y-%m-%d'),
                        'reply_content_summary': f'[{req_type}] {reply_body[:200]}',
                        'next_action': f'Send Stage {detected_stage} info',
                        'status': 'replied',
                        'detected_stage': str(detected_stage),
                    }

                    for key, val in updates.items():
                        if key in headers:
                            tracking_sheet.update_cell(idx, headers.index(key) + 1, val)

                    updated += 1
                    time_mod.sleep(0.5)
                    break

        try:
            from daemon_integration import _load_activities, ACTIVITY_FILE
            import json
            activities = _load_activities()
            activities.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'check_replies',
                'found': len(replies),
                'updated': updated,
                'source': 'manual',
            })
            activities = activities[-200:]
            with open(ACTIVITY_FILE, 'w') as f:
                json.dump(activities, f, indent=2)
        except Exception:
            pass

        logger.info(f"Manual reply check: {updated} updated from {len(replies)} replies")
        flash(f'Found {len(replies)} replies, updated {updated} email records!', 'success')

    except Exception as e:
        logger.error(f"Manual reply check failed: {e}")
        safe_flash_error(e, 'Check replies')

    return redirect(url_for('auto_reply.auto_reply_page'))


@auto_reply_bp.route('/auto-reply/clear-log', methods=['POST'])
@login_required
def clear_log():
    """Clear the daemon log file."""
    try:
        log_file = os.path.join(PROJECT_ROOT, 'logs', 'auto_reply.log')
        if os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write(f"Log cleared at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        flash('Log file cleared.', 'info')
    except Exception as e:
        safe_flash_error(e, 'Clear log')

    return redirect(url_for('auto_reply.auto_reply_page'))


@auto_reply_bp.route('/auto-reply/clear-activity', methods=['POST'])
@login_required
def clear_activity():
    """Clear the activity history."""
    try:
        activity_file = os.path.join(PROJECT_ROOT, 'logs', 'auto_reply_activity.json')
        if os.path.exists(activity_file):
            import json
            with open(activity_file, 'w') as f:
                json.dump([], f)
        flash('Activity history cleared.', 'info')
    except Exception as e:
        safe_flash_error(e, 'Clear activity')

    return redirect(url_for('auto_reply.auto_reply_page'))


@auto_reply_bp.route('/auto-reply/start', methods=['POST'])
@login_required
def start_daemon():
    """Start the auto-reply monitor daemon."""
    try:
        from daemon_integration import get_daemon_status
        status = get_daemon_status()

        if status.get('running'):
            flash('Daemon is already running.', 'info')
            return redirect(url_for('auto_reply.auto_reply_page'))

        monitor_script = os.path.join(PROJECT_ROOT, 'auto_reply_monitor.py')
        log_file = os.path.join(PROJECT_ROOT, 'logs', 'auto_reply.log')

        os.makedirs(os.path.join(PROJECT_ROOT, 'logs'), exist_ok=True)

        with open(log_file, 'a') as lf:
            proc = subprocess.Popen(
                ['python3', '-u', monitor_script],
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=PROJECT_ROOT,
                start_new_session=True,
            )

        logger.info(f"Started auto-reply daemon, PID: {proc.pid}")
        flash(f'Auto-reply daemon started (PID: {proc.pid}).', 'success')

    except Exception as e:
        logger.error(f"Failed to start daemon: {e}")
        flash(f'Failed to start daemon: {e}', 'danger')

    return redirect(url_for('auto_reply.auto_reply_page'))


@auto_reply_bp.route('/auto-reply/stop', methods=['POST'])
@login_required
def stop_daemon():
    """Stop the auto-reply monitor daemon."""
    try:
        from daemon_integration import get_daemon_status

        status = get_daemon_status()
        if not status.get('running'):
            flash('Daemon is not running.', 'info')
            return redirect(url_for('auto_reply.auto_reply_page'))

        pid = status.get('pid')
        if pid:
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Stopped auto-reply daemon, PID: {pid}")
            flash(f'Auto-reply daemon stopped (PID: {pid}).', 'warning')

            pid_file = os.path.join(PROJECT_ROOT, 'logs', 'auto_reply.pid')
            if os.path.exists(pid_file):
                os.unlink(pid_file)
        else:
            flash('Cannot determine daemon PID.', 'danger')

    except ProcessLookupError:
        flash('Daemon process not found (may have already stopped).', 'info')
        pid_file = os.path.join(PROJECT_ROOT, 'logs', 'auto_reply.pid')
        if os.path.exists(pid_file):
            os.unlink(pid_file)
    except Exception as e:
        logger.error(f"Failed to stop daemon: {e}")
        flash(f'Failed to stop daemon: {e}', 'danger')

    return redirect(url_for('auto_reply.auto_reply_page'))


@auto_reply_bp.route('/auto-reply/status')
@login_required
def daemon_status_api():
    """API endpoint returning all live data for real-time AJAX refresh."""
    followup_days = get_user_config('followup_days', 3)
    result = {
        'daemon_status': {'running': False, 'pid': None, 'status': 'STOPPED'},
        'statistics': {},
        'recent_activity': [],
        'log_lines': [],
        'reply_inbox': [],
        'reply_stats': {'total_replies': 0, 'needs_action': 0, 'hot_leads': 0, 'declined': 0},
        'email_summary': {'total': 0, 'sent': 0, 'queued': 0, 'stale': 0},
        'timestamp': datetime.now().strftime('%H:%M:%S'),
    }

    try:
        from daemon_integration import (
            get_daemon_status, get_daemon_statistics,
            get_recent_activity, get_log_tail
        )
        result['daemon_status'] = get_daemon_status()
        result['statistics'] = get_daemon_statistics()
        result['recent_activity'] = get_recent_activity(limit=20)
        result['log_lines'] = get_log_tail(lines=40)
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Status API daemon error: {e}")

    try:
        sheets = get_sheets()
        tracking_sheet = sheets.get_worksheet('Email_Tracking')
        emails = tracking_sheet.get_all_records()
        customers = sheets.get_customers()
        customer_map = {str(c.get('id', '')): c for c in customers}

        for e in emails:
            if e.get('replied') != 'yes':
                continue
            result['reply_stats']['total_replies'] += 1

            reply_summary = str(e.get('reply_content_summary', ''))
            req_type = ''
            if reply_summary.startswith('[') and ']' in reply_summary:
                req_type = reply_summary[1:reply_summary.index(']')]

            if req_type in ('Quotation Request', 'Sample Request', 'Contract Request', 'Repeat Order'):
                result['reply_stats']['hot_leads'] += 1
            elif req_type == 'Declined':
                result['reply_stats']['declined'] += 1

            status = e.get('status', '')
            if status == 'replied':
                result['reply_stats']['needs_action'] += 1
                customer = customer_map.get(str(e.get('customer_id', '')), {})
                detected = str(e.get('detected_stage', ''))
                detected_info = PIPELINE_STAGES.get(int(detected), {}) if detected.isdigit() else {}

                result['reply_inbox'].append({
                    'email_id': e.get('email_id', ''),
                    'customer_id': e.get('customer_id', ''),
                    'company_name': e.get('company_name', customer.get('company_name', '-')),
                    'contact_email': e.get('contact_email', ''),
                    'subject': e.get('subject', ''),
                    'reply_date': e.get('reply_date', ''),
                    'request_type': req_type,
                    'reply_summary': reply_summary[:80],
                    'detected_stage': detected,
                    'detected_stage_name': detected_info.get('name', ''),
                    'detected_attachments': detected_info.get('attachments', []),
                    'status': status,
                    'engagement': customer.get('engagement_level', ''),
                })

        result['reply_inbox'].sort(key=lambda x: x.get('reply_date', ''), reverse=True)
        result['reply_inbox'] = result['reply_inbox'][:20]

        now = datetime.now()
        for e in emails:
            result['email_summary']['total'] += 1
            st = e.get('status', '')
            if st == 'sent':
                result['email_summary']['sent'] += 1
                sent_date_str = e.get('sent_date', '')
                if sent_date_str and e.get('replied', 'no') != 'yes':
                    try:
                        sent_date = datetime.strptime(sent_date_str, '%Y-%m-%d')
                        current_stage = int(e.get('pipeline_stage', 1)) if str(e.get('pipeline_stage', '1')).isdigit() else 1
                        delay = PIPELINE_STAGES.get(current_stage, {}).get('followup_days', followup_days)
                        if delay > 0 and (now - sent_date).days >= delay:
                            result['email_summary']['stale'] += 1
                    except ValueError:
                        pass
            elif st == 'queued':
                result['email_summary']['queued'] += 1
    except Exception as e:
        logger.error(f"Status API sheets error: {e}")

    return jsonify(result)
