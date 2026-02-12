"""Compose email routes."""

import time
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app_core import (login_required, get_sheets, cached_get_customers,
                      EmailPersonalizationEngine, API_KEY, PIPELINE_STAGES, create_email_log,
                      SENDER_NAME, SENDER_TITLE, COMPANY_NAME, COMPANY_PHONE,
                      COMPANY_WEBSITE, COMPANY_ADDRESS, SENDER_EMAIL, is_valid_email, logger,
                      safe_flash_error)
from services.email_service import send_email_via_gmail

compose_bp = Blueprint('compose', __name__)


@compose_bp.route('/compose')
@login_required
def compose_page():
    try:
        customers = cached_get_customers()
    except Exception as e:
        return render_template('compose.html', active_page='compose', error=str(e),
                               customers=[], selected_id='', pipeline_stages=PIPELINE_STAGES,
                               generated=None, gen_customer_id='', gen_stage='1', attachments_val='',
                               sender_name=SENDER_NAME, sender_title=SENDER_TITLE,
                               company_name=COMPANY_NAME, company_phone=COMPANY_PHONE,
                               company_website=COMPANY_WEBSITE, company_address=COMPANY_ADDRESS)

    selected_id = request.args.get('id', '')
    generated = session.pop('generated_email', None)
    gen_customer_id = session.pop('gen_customer_id', '')
    gen_stage = session.pop('gen_stage', '1')

    attachments_val = ''
    if generated:
        atts = generated.get('attachments', [])
        attachments_val = ';'.join(atts) if isinstance(atts, list) else str(atts)

    return render_template('compose.html',
        active_page='compose',
        customers=customers,
        selected_id=selected_id,
        pipeline_stages=PIPELINE_STAGES,
        generated=generated,
        gen_customer_id=gen_customer_id,
        gen_stage=gen_stage,
        attachments_val=attachments_val,
        today=datetime.now().strftime('%Y-%m-%d'),
        sender_name=SENDER_NAME, sender_title=SENDER_TITLE,
        company_name=COMPANY_NAME, company_phone=COMPANY_PHONE,
        company_website=COMPANY_WEBSITE, company_address=COMPANY_ADDRESS,
    )


@compose_bp.route('/compose/generate', methods=['POST'])
@login_required
def generate_email():
    customer_id = request.form.get('customer_id', '')
    stage = int(request.form.get('stage', 1))
    context = request.form.get('context', '')

    try:
        customers = cached_get_customers()
        customer = next((c for c in customers if str(c.get('id')) == customer_id), None)

        if not customer:
            flash('Customer not found.', 'danger')
            return redirect(url_for('compose.compose_page'))

        research = {
            'summary': customer.get('research_summary', ''),
            'industry': customer.get('tags', 'Manufacturing'),
            'pain_points': customer.get('pain_points', '')
        }

        engine = EmailPersonalizationEngine(API_KEY)
        email = engine.generate_email(customer, research, stage, context)

        if email:
            session['generated_email'] = email
            session['gen_customer_id'] = customer_id
            session['gen_stage'] = str(stage)
            flash('Email generated successfully!', 'success')
        else:
            flash('Failed to generate email.', 'danger')
    except Exception as e:
        logger.error(f"Email generation failed: {e}")
        safe_flash_error(e, 'Email operation')

    return redirect(url_for('compose.compose_page', id=customer_id))


@compose_bp.route('/compose/approve', methods=['POST'])
@login_required
def approve_email():
    customer_id = request.form.get('customer_id', '')
    subject = request.form.get('subject', '')
    body = request.form.get('body', '')
    stage = request.form.get('stage', '1')
    attachments = request.form.get('attachments', '')

    try:
        sheets = get_sheets()
        customers = sheets.get_customers()
        customer = next((c for c in customers if str(c.get('id')) == customer_id), None)

        scheduled_date = request.form.get('scheduled_date', '')
        email_log = create_email_log(customer_id, customer, subject, body, stage,
                                     attachments=attachments, status='queued')
        if scheduled_date:
            email_log['scheduled_date'] = scheduled_date
        sheets.log_email(email_log)
        logger.info(f"Email queued for {customer.get('company_name', '')}")
        msg = 'Email approved and queued for sending!'
        if scheduled_date:
            msg = f'Email scheduled for {scheduled_date}!'
        flash(msg, 'success')
    except Exception as e:
        safe_flash_error(e, 'Email operation')

    return redirect(url_for('tracking.tracking_page'))


@compose_bp.route('/compose/send_now', methods=['POST'])
@login_required
def send_now():
    customer_id = request.form.get('customer_id', '')
    subject = request.form.get('subject', '')
    body = request.form.get('body', '')
    stage = request.form.get('stage', '1')
    attachments_str = request.form.get('attachments', '')

    try:
        sheets = get_sheets()
        customers = sheets.get_customers()
        customer = next((c for c in customers if str(c.get('id')) == customer_id), None)

        if not customer:
            flash('Customer not found.', 'danger')
            return redirect(url_for('compose.compose_page'))

        to_email = customer.get('contact_email', '')
        company_name = customer.get('company_name', customer_id)
        if not to_email or not is_valid_email(to_email):
            flash(f'{company_name}: invalid email address "{to_email}". Please fix it in Google Sheets (Customers tab, contact_email column).', 'danger')
            return redirect(url_for('compose.compose_page', id=customer_id))

        attachment_files = [a.strip() for a in attachments_str.split(';') if a.strip()] if attachments_str else []
        msg_id, error = send_email_via_gmail(to_email, subject, body, attachment_files,
                                              sender_name=SENDER_NAME, sender_email=SENDER_EMAIL)

        if error:
            flash(f'Failed to send: {error}', 'danger')
            return redirect(url_for('compose.compose_page', id=customer_id))

        email_log = create_email_log(customer_id, customer, subject, body, stage,
                                     attachments=attachments_str, status='sent',
                                     gmail_msg_id=msg_id or '')
        sheets.log_email(email_log)
        logger.info(f"Email sent to {to_email}")
        flash(f'Email sent to {to_email} successfully!', 'success')

    except Exception as e:
        safe_flash_error(e, 'Email operation')

    return redirect(url_for('tracking.tracking_page'))
