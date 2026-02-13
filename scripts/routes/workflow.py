"""Workflow automation routes."""

import sys
import threading
from flask import Blueprint, render_template, jsonify
from app_core import login_required, get_workflow_status, workflow_lock, logger, get_current_user

workflow_bp = Blueprint('workflow', __name__)


class LogCapture:
    def __init__(self, original, user_id):
        self.original = original
        self.user_id = user_id

    def write(self, text):
        text = text.strip()
        if text:
            status = get_workflow_status(self.user_id)
            with workflow_lock:
                status['log'].append(text)
        self.original.write(text + '\n')

    def flush(self):
        self.original.flush()


@workflow_bp.route('/workflow')
@login_required
def workflow_page():
    return render_template('workflow.html', active_page='workflow')


@workflow_bp.route('/workflow/run', methods=['POST'])
@login_required
def run_workflow():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Session expired. Please log in again.'})

    user_id = user.id
    status = get_workflow_status(user_id)

    with workflow_lock:
        if status['running']:
            return jsonify({'error': 'Workflow is already running.'})

    def _run():
        with workflow_lock:
            status['running'] = True
            status['log'] = []
            status['completed'] = False
            status['error'] = None

        old_stdout = sys.stdout
        sys.stdout = LogCapture(old_stdout, user_id)

        try:
            from main_automation import main_workflow
            main_workflow()
            with workflow_lock:
                status['completed'] = True
        except Exception as e:
            logger.error(f"Workflow failed for user {user_id}: {e}")
            with workflow_lock:
                status['error'] = str(e)
                status['log'].append(f"Error: {e}")
        finally:
            sys.stdout = old_stdout
            with workflow_lock:
                status['running'] = False

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({'status': 'started'})


@workflow_bp.route('/workflow/status')
@login_required
def workflow_status_endpoint():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Session expired'})

    status = get_workflow_status(user.id)
    with workflow_lock:
        return jsonify(dict(status))
