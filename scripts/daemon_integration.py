"""
Integration module between auto-reply daemon and web UI.
Reads PID file, activity JSON log, and Google Sheets for real stats.
"""

import os
import json
import signal
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = Path(PROJECT_ROOT) / 'logs'
PID_FILE = LOG_DIR / 'auto_reply.pid'
ACTIVITY_FILE = LOG_DIR / 'auto_reply_activity.json'
LOG_FILE = LOG_DIR / 'auto_reply.log'


def get_daemon_status():
    """Check if daemon is running via PID file."""
    try:
        if not PID_FILE.exists():
            return {'running': False, 'pid': None, 'status': 'STOPPED'}

        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        # Check if process is alive
        os.kill(pid, 0)
        return {'running': True, 'pid': pid, 'status': 'RUNNING'}

    except (ProcessLookupError, ValueError):
        # Process not running, clean up stale PID file
        if PID_FILE.exists():
            PID_FILE.unlink()
        return {'running': False, 'pid': None, 'status': 'STOPPED'}
    except PermissionError:
        # Process exists but we can't signal it
        return {'running': True, 'pid': None, 'status': 'RUNNING'}
    except Exception:
        return {'running': False, 'pid': None, 'status': 'UNKNOWN'}


def get_daemon_statistics():
    """Get real statistics from activity log."""
    stats = {
        'total_processed': 0,
        'total_sent': 0,
        'total_skipped': 0,
        'total_failed': 0,
        'total_checks': 0,
        'total_stale': 0,
        'last_check': None,
        'success_rate': 0,
    }

    activities = _load_activities()
    if not activities:
        return stats

    for a in activities:
        action = a.get('action', '')
        if action == 'check_replies':
            stats['total_checks'] += 1
            stats['total_processed'] += a.get('found', 0)
            stats['total_sent'] += a.get('updated', 0)
            stats['last_check'] = a.get('timestamp', '')
        elif action == 'reply_processed':
            result = a.get('result', '')
            if result == 'updated':
                pass  # counted in check_replies
        elif action == 'check_stale':
            stats['total_stale'] += a.get('stale_count', 0)
        elif action == 'error':
            stats['total_failed'] += 1

    if stats['total_processed'] > 0:
        stats['success_rate'] = round(stats['total_sent'] / stats['total_processed'] * 100, 1)

    return stats


def get_recent_activity(limit=15):
    """Get recent activity entries from JSON log."""
    activities = _load_activities()
    if not activities:
        return []

    # Filter to interesting entries (not daemon start/stop)
    interesting = [a for a in activities if a.get('action') in
                   ('reply_processed', 'check_replies', 'check_stale', 'error')]

    result = []
    for a in interesting[-limit:]:
        action = a.get('action', '')
        if action == 'reply_processed':
            result.append({
                'time': a.get('timestamp', '-'),
                'from': a.get('from', '-'),
                'company': a.get('company', ''),
                'stage': f"{a.get('detected_stage', '?')} ({a.get('stage_name', '')})",
                'type': a.get('request_type', ''),
                'result': 'sent',
            })
        elif action == 'check_replies':
            result.append({
                'time': a.get('timestamp', '-'),
                'from': 'System',
                'company': '',
                'stage': '-',
                'type': f"Found {a.get('found', 0)}, Updated {a.get('updated', 0)}",
                'result': 'check',
            })
        elif action == 'check_stale':
            count = a.get('stale_count', 0)
            result.append({
                'time': a.get('timestamp', '-'),
                'from': 'System',
                'company': '',
                'stage': '-',
                'type': f"{count} stale email(s) found",
                'result': 'stale' if count > 0 else 'check',
            })
        elif action == 'error':
            result.append({
                'time': a.get('timestamp', '-'),
                'from': 'System',
                'company': '',
                'stage': '-',
                'type': a.get('error', 'Unknown error')[:60],
                'result': 'failed',
            })

    return list(reversed(result))


def get_stage_distribution():
    """Get distribution of processed replies by detected stage."""
    activities = _load_activities()
    stages = {}
    for a in activities:
        if a.get('action') == 'reply_processed':
            stage = a.get('detected_stage')
            if stage:
                stages[stage] = stages.get(stage, 0) + 1
    return stages


def get_log_tail(lines=50):
    """Get last N lines of the log file."""
    if not LOG_FILE.exists():
        return []
    try:
        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()
        return [line.rstrip() for line in all_lines[-lines:]]
    except Exception:
        return []


def _load_activities():
    """Load activity entries from JSON file."""
    if not ACTIVITY_FILE.exists():
        return []
    try:
        with open(ACTIVITY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return []
