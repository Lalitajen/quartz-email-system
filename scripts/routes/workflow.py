"""Workflow automation routes."""

import sys
import threading
from flask import Blueprint, render_template, jsonify
from app_core import login_required, workflow_status, workflow_lock, logger

workflow_bp = Blueprint('workflow', __name__)


class LogCapture:
    def __init__(self, original):
        self.original = original

    def write(self, text):
        text = text.strip()
        if text:
            with workflow_lock:
                workflow_status['log'].append(text)
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
    with workflow_lock:
        if workflow_status['running']:
            return jsonify({'error': 'Workflow is already running.'})

    def _run():
        with workflow_lock:
            workflow_status['running'] = True
            workflow_status['log'] = []
            workflow_status['completed'] = False
            workflow_status['error'] = None

        old_stdout = sys.stdout
        sys.stdout = LogCapture(old_stdout)

        try:
            from main_automation import main_workflow
            main_workflow()
            with workflow_lock:
                workflow_status['completed'] = True
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            with workflow_lock:
                workflow_status['error'] = str(e)
                workflow_status['log'].append(f"Error: {e}")
        finally:
            sys.stdout = old_stdout
            with workflow_lock:
                workflow_status['running'] = False

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({'status': 'started'})


@workflow_bp.route('/workflow/status')
@login_required
def workflow_status_endpoint():
    with workflow_lock:
        return jsonify(dict(workflow_status))
