"""Batch send routes."""

import time
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app_core import (login_required, get_sheets, cached_get_customers,
                      EmailPersonalizationEngine, API_KEY, PIPELINE_STAGES,
                      SENDER_NAME, SENDER_TITLE, COMPANY_NAME, SENDER_EMAIL,
                      SPAM_DOMAINS, create_email_log, is_valid_email, logger)
from services.email_service import send_email_via_gmail

batch_send_bp = Blueprint('batch_send', __name__)


@batch_send_bp.route('/batch_send')
@login_required
def batch_send_page():
    try:
        customers = cached_get_customers()
    except Exception as e:
        return render_template('batch_send.html', active_page='batch_send', error=str(e),
                               pipeline_stages=PIPELINE_STAGES, stage_groups={},
                               total_customers=0, sender_name=SENDER_NAME,
                               sender_title=SENDER_TITLE, company_name=COMPANY_NAME)

    stage_groups = {}
    for c in customers:
        stage = int(c.get('pipeline_stage', 1)) if str(c.get('pipeline_stage', '1')).isdigit() else 1
        stage_groups.setdefault(stage, []).append(c)

    return render_template('batch_send.html',
        active_page='batch_send',
        pipeline_stages=PIPELINE_STAGES,
        stage_groups=stage_groups,
        total_customers=len(customers),
        sender_name=SENDER_NAME,
        sender_title=SENDER_TITLE,
        company_name=COMPANY_NAME,
    )


@batch_send_bp.route('/batch_send/run', methods=['POST'])
@login_required
def batch_send_run():
    stage = int(request.form.get('stage', 1))
    customer_ids = request.form.getlist('customer_ids')
    if len(customer_ids) == 1 and ',' in customer_ids[0]:
        customer_ids = [cid.strip() for cid in customer_ids[0].split(',') if cid.strip()]

    if not customer_ids:
        flash('No customers selected.', 'warning')
        return redirect(url_for('batch_send.batch_send_page'))

    try:
        sheets = get_sheets()
        customers = sheets.get_customers()
        engine = EmailPersonalizationEngine(API_KEY)
        stage_info = PIPELINE_STAGES.get(stage, {})
        attachment_files = stage_info.get('attachments', [])

        sent_count = 0
        fail_count = 0

        for cid in customer_ids:
            customer = next((c for c in customers if str(c.get('id')) == cid), None)
            if not customer:
                continue

            to_email = customer.get('contact_email', '')
            if not to_email or not is_valid_email(to_email):
                logger.warning(f"Skipped {customer.get('company_name', cid)}: missing or invalid email '{to_email}'")
                fail_count += 1
                continue
            if any(d in to_email.lower() for d in SPAM_DOMAINS):
                logger.warning(f"Skipped {customer.get('company_name', cid)}: spam domain ({to_email})")
                fail_count += 1
                continue

            research = {
                'summary': customer.get('research_summary', ''),
                'industry': customer.get('tags', 'Manufacturing'),
                'pain_points': customer.get('pain_points', '')
            }
            email_data = engine.generate_email(customer, research, stage)

            if not email_data:
                fail_count += 1
                continue

            subject = email_data.get('subject', '')
            body = email_data.get('body', '')

            msg_id, error = send_email_via_gmail(to_email, subject, body, attachment_files,
                                                  sender_name=SENDER_NAME, sender_email=SENDER_EMAIL)
            if error:
                logger.warning(f"Send failed for {customer.get('company_name', cid)} ({to_email}): {error}")
                fail_count += 1
                continue

            email_log = create_email_log(cid, customer, subject, body, stage,
                                         attachments=';'.join(attachment_files),
                                         status='sent', reviewed_by='auto_approved',
                                         gmail_msg_id=msg_id or '',
                                         confidence=email_data.get('confidence_score', ''))
            import uuid
            email_log['email_id'] = f"EMAIL{int(time.time())}_{cid}_{uuid.uuid4().hex[:4]}"
            sheets.log_email(email_log)
            sent_count += 1
            time.sleep(1)

        logger.info(f"Batch send: {sent_count} sent, {fail_count} failed")
        flash(f'Batch complete! Sent: {sent_count}, Failed: {fail_count}',
              'success' if fail_count == 0 else 'warning')

    except Exception as e:
        logger.error(f"Batch send error: {e}")
        flash(f'Batch send error: {e}', 'danger')

    return redirect(url_for('tracking.tracking_page'))
