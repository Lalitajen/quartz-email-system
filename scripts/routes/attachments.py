"""Attachment management routes."""

import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from app_core import (login_required, PIPELINE_STAGES, PROJECT_ROOT, safe_attachment_path, logger)

attachments_bp = Blueprint('attachments', __name__)


@attachments_bp.route('/attachments')
@login_required
def attachments_page():
    attachments_dir = os.path.join(PROJECT_ROOT, 'attachments')
    pdf_files = []
    if os.path.exists(attachments_dir):
        pdf_files = sorted(f for f in os.listdir(attachments_dir) if f.endswith('.pdf'))

    pdf_file_info = []
    for pdf in pdf_files:
        file_path = os.path.join(attachments_dir, pdf)
        file_size = os.path.getsize(file_path) / 1024
        file_date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M')

        used_in_stages = [str(sn) for sn, si in PIPELINE_STAGES.items() if pdf in si.get('attachments', [])]
        if used_in_stages:
            usage = f'<span class="badge bg-info">Used in: {", ".join(used_in_stages)}</span>'
        else:
            usage = '<span class="badge bg-secondary">Unused</span>'

        pdf_file_info.append({
            'name': pdf,
            'size': f'{file_size:.1f}',
            'date': file_date,
            'usage': usage,
        })

    return render_template('attachments.html',
        active_page='attachments',
        pipeline_stages=PIPELINE_STAGES,
        pdf_files=pdf_files,
        pdf_file_info=pdf_file_info,
        pipeline_stages_json=json.dumps({str(k): v for k, v in PIPELINE_STAGES.items()}),
    )


@attachments_bp.route('/attachments/upload', methods=['POST'])
@login_required
def upload_attachment():
    if 'pdf_file' not in request.files:
        flash('No file uploaded', 'danger')
        return redirect(url_for('attachments.attachments_page'))

    file = request.files['pdf_file']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('attachments.attachments_page'))

    if not file.filename.endswith('.pdf'):
        flash('Only PDF files are allowed', 'danger')
        return redirect(url_for('attachments.attachments_page'))

    # Check file size (10 MB limit)
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 10 * 1024 * 1024:
        flash('File too large (max 10 MB)', 'danger')
        return redirect(url_for('attachments.attachments_page'))

    safe_name = secure_filename(file.filename)
    if not safe_name:
        flash('Invalid filename', 'danger')
        return redirect(url_for('attachments.attachments_page'))

    attachments_dir = os.path.join(PROJECT_ROOT, 'attachments')
    os.makedirs(attachments_dir, exist_ok=True)
    file.save(os.path.join(attachments_dir, safe_name))

    logger.info(f"Uploaded attachment: {safe_name}")
    flash(f'Successfully uploaded {safe_name}', 'success')
    return redirect(url_for('attachments.attachments_page'))


@attachments_bp.route('/attachments/download/<filename>')
@login_required
def download_attachment(filename):
    file_path = safe_attachment_path(filename)
    if not file_path:
        flash('Invalid filename', 'danger')
        return redirect(url_for('attachments.attachments_page'))

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found', 'danger')
        return redirect(url_for('attachments.attachments_page'))


@attachments_bp.route('/attachments/delete/<filename>', methods=['POST'])
@login_required
def delete_attachment(filename):
    file_path = safe_attachment_path(filename)
    if not file_path:
        return jsonify({'success': False, 'error': 'Invalid filename'})

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted attachment: {filename}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'File not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@attachments_bp.route('/attachments/update-stage', methods=['POST'])
@login_required
def update_stage_attachments():
    stage_number = int(request.form.get('stage_number'))
    attachments = request.form.getlist('attachments')

    if stage_number in PIPELINE_STAGES:
        PIPELINE_STAGES[stage_number]['attachments'] = attachments

        config_path = os.path.join(PROJECT_ROOT, 'config', 'pipeline_config.json')
        with open(config_path, 'w') as f:
            json.dump(PIPELINE_STAGES, f, indent=2)

        logger.info(f"Updated stage {stage_number} attachments: {attachments}")
        flash(f'Stage {stage_number} attachments updated!', 'success')
    else:
        flash('Invalid stage number.', 'danger')

    return redirect(url_for('attachments.attachments_page'))
