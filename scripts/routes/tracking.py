"""Email tracking and reply checking routes."""

import csv
import io
import time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from app_core import (login_required, get_sheets, PIPELINE_STAGES, SPAM_DOMAINS,
                      EmailTracker, EmailPersonalizationEngine, get_api_key,
                      get_sender_info, get_user_config, create_email_log,
                      classify_reply, classify_reply_smart, logger, safe_flash_error,
                      get_gmail_service_for_user)
from services.email_service import send_email_via_gmail

tracking_bp = Blueprint('tracking', __name__)

PER_PAGE = 25


@tracking_bp.route('/tracking')
@login_required
def tracking_page():
    followup_days = get_user_config('followup_days', 3)
    try:
        sheets = get_sheets()
        sheet_emails = sheets.get_worksheet('Email_Tracking')
        emails = sheet_emails.get_all_records()
    except Exception as e:
        return render_template('tracking.html', active_page='tracking', error=str(e),
                               emails=[], tab='all', total_count=0,
                               n_pending=0, n_queued=0, n_sent=0, n_replied=0,
                               n_followups=0, followup_queue=[],
                               pipeline_stages=PIPELINE_STAGES, page=1, total_pages=1)

    tab = request.args.get('tab', 'all')
    page = request.args.get('page', 1, type=int)

    if tab == 'followups':
        return redirect(url_for('tracking.followup_queue'))

    if tab == 'pending':
        filtered = [e for e in emails if e.get('reviewed_by') == 'pending_review']
    elif tab == 'sent':
        filtered = [e for e in emails if e.get('status') == 'sent']
    elif tab == 'queued':
        filtered = [e for e in emails if e.get('status') == 'queued']
    elif tab == 'replied':
        filtered = [e for e in emails if e.get('replied') == 'yes']
    else:
        filtered = emails

    n_pending = len([e for e in emails if e.get('reviewed_by') == 'pending_review'])
    n_queued = len([e for e in emails if e.get('status') == 'queued'])
    n_sent = len([e for e in emails if e.get('status') == 'sent'])
    n_replied = len([e for e in emails if e.get('replied') == 'yes'])

    now = datetime.now()
    n_followups = 0
    for e in emails:
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
        delay = PIPELINE_STAGES.get(current_stage, {}).get('followup_days', followup_days)
        if delay > 0 and (now - sent_date).days >= delay:
            n_followups += 1

    total_count = len(filtered)
    total_pages = max(1, (total_count + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * PER_PAGE
    paginated = filtered[start:start + PER_PAGE]

    return render_template('tracking.html',
        active_page='tracking',
        emails=paginated,
        tab=tab,
        total_count=len(emails),
        n_pending=n_pending, n_queued=n_queued, n_sent=n_sent, n_replied=n_replied,
        n_followups=n_followups,
        followup_queue=[],
        pipeline_stages=PIPELINE_STAGES,
        page=page,
        total_pages=total_pages,
    )


@tracking_bp.route('/tracking/check_replies')
@login_required
def check_replies_now():
    try:
        gmail_service = get_gmail_service_for_user()
        tracker = EmailTracker.__new__(EmailTracker)
        tracker.service = gmail_service

        replies = tracker.check_new_replies(since_hours=24)

        if not replies:
            flash('No new replies found.', 'info')
            return redirect(url_for('tracking.tracking_page'))

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

            # Find matching customer record first for context
            matched_record = None
            for record in tracking_records:
                record_email = record.get('contact_email', '').lower()
                if record_email and record_email == from_email.lower():
                    matched_record = record
                    break

            # Use AI-powered classification with customer context
            if matched_record:
                customer_context = {
                    'company_name': matched_record.get('company_name', ''),
                    'industry': matched_record.get('industry', ''),
                }
                current_stage = int(matched_record.get('pipeline_stage', 1)) if str(matched_record.get('pipeline_stage', '')).isdigit() else 1

                classification = classify_reply_smart(
                    reply_body=reply_body,
                    subject=reply.get('subject', ''),
                    current_stage=current_stage,
                    customer_context=customer_context,
                    use_ai=True
                )

                req_type = classification['intent']
                detected_stage = classification['stage']
                confidence = classification['confidence']
                urgency = classification.get('urgency_level', 'medium')
                sentiment = classification.get('sentiment', 'neutral')
                buying_signals = classification.get('buying_signals', [])

                logger.info(f"AI Classification: {req_type} (stage {detected_stage}, confidence {confidence:.2f}, urgency {urgency}, sentiment {sentiment})")

                if buying_signals:
                    logger.info(f"Buying signals detected: {buying_signals}")
            else:
                # Fallback to simple keyword classification
                req_type, detected_stage = classify_reply(reply_body)
                confidence = 0.5

            if detected_stage is None:
                detected_stage = 2

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
                    time.sleep(0.5)
                    break

        logger.info(f"Checked replies: {updated} updated")
        flash(f'Found and processed {updated} replies!', 'success')

    except Exception as e:
        logger.error(f"Reply check failed: {e}")
        safe_flash_error(e, 'Check replies')

    return redirect(url_for('tracking.tracking_page'))


@tracking_bp.route('/tracking/follow_up', methods=['POST'])
@login_required
def follow_up_send():
    email_id = request.form.get('email_id', '')
    customer_id = request.form.get('customer_id', '')
    stage = int(request.form.get('stage', 1))

    try:
        sheets = get_sheets()
        customers = sheets.get_customers()
        customer = next((c for c in customers if str(c.get('id')) == customer_id), None)

        if not customer:
            flash('Customer not found.', 'danger')
            return redirect(url_for('tracking.tracking_page'))

        to_email = customer.get('contact_email', '')
        if not to_email:
            flash('Customer has no email.', 'danger')
            return redirect(url_for('tracking.tracking_page'))

        stage_info = PIPELINE_STAGES.get(stage, {})
        attachment_files = stage_info.get('attachments', [])

        engine = EmailPersonalizationEngine(get_api_key())
        research = {
            'summary': customer.get('research_summary', ''),
            'industry': customer.get('tags', 'Manufacturing'),
            'pain_points': customer.get('pain_points', '')
        }

        context = f"This is a follow-up email. Customer replied and requested info matching Stage {stage} ({stage_info.get('name', '')}). Send appropriate information with attachments: {', '.join(attachment_files)}"
        email_data = engine.generate_email(customer, research, stage, context)

        if not email_data:
            flash('Failed to generate follow-up email.', 'danger')
            return redirect(url_for('tracking.tracking_page'))

        subject = email_data.get('subject', '')
        body = email_data.get('body', '')

        sender = get_sender_info()
        gmail_service = get_gmail_service_for_user()
        msg_id, error = send_email_via_gmail(to_email, subject, body, attachment_files,
                                              sender_name=sender['sender_name'],
                                              sender_email=sender['sender_email'],
                                              gmail_service=gmail_service)
        if error:
            flash(f'Failed to send: {error}', 'danger')
            return redirect(url_for('tracking.tracking_page'))

        email_log = create_email_log(customer_id, customer, subject, body, stage,
                                     attachments=';'.join(attachment_files),
                                     status='sent', email_type='follow_up',
                                     reviewed_by='auto_approved',
                                     gmail_msg_id=msg_id or '',
                                     confidence=email_data.get('confidence_score', ''))
        import uuid
        email_log['email_id'] = f"FU{int(time.time())}_{uuid.uuid4().hex[:6]}"
        email_log['reply_content_summary'] = f'Follow-up to {email_id}'
        sheets.log_email(email_log)

        tracking_sheet = sheets.get_worksheet('Email_Tracking')
        records = tracking_sheet.get_all_records()
        headers = tracking_sheet.row_values(1)
        for idx, record in enumerate(records, start=2):
            if record.get('email_id') == email_id:
                if 'status' in headers:
                    tracking_sheet.update_cell(idx, headers.index('status') + 1, 'followed_up')
                if 'next_action' in headers:
                    tracking_sheet.update_cell(idx, headers.index('next_action') + 1, f'Sent Stage {stage} follow-up')
                break

        sheets.update_customer(customer_id, {'pipeline_stage': stage})

        logger.info(f"Follow-up sent to {to_email} at stage {stage}")
        flash(f'Follow-up sent to {to_email}! Stage {stage} ({stage_info.get("name", "")}) with {", ".join(attachment_files)}', 'success')

    except Exception as e:
        logger.error(f"Follow-up failed: {e}")
        safe_flash_error(e, 'Tracking operation')

    return redirect(url_for('tracking.tracking_page'))


@tracking_bp.route('/tracking/auto_followup')
@login_required
def auto_followup():
    """Find emails sent more than followup_days ago with no reply and send follow-ups."""
    followup_days = get_user_config('followup_days', 3)
    try:
        sheets = get_sheets()
        tracking_sheet = sheets.get_worksheet('Email_Tracking')
        emails = tracking_sheet.get_all_records()
        headers = tracking_sheet.row_values(1)
        customers = sheets.get_customers()

        now = datetime.now()

        stale = []
        for idx, e in enumerate(emails, start=2):
            sent_date_str = e.get('sent_date', '')
            if not sent_date_str:
                continue
            try:
                sent_date = datetime.strptime(sent_date_str, '%Y-%m-%d')
            except ValueError:
                continue
            if e.get('status') != 'sent' or e.get('replied', 'no') == 'yes':
                continue

            current_stage = int(e.get('pipeline_stage', 1)) if str(e.get('pipeline_stage', '1')).isdigit() else 1
            delay_days = PIPELINE_STAGES.get(current_stage, {}).get('followup_days', followup_days)
            if delay_days == 0:
                continue

            if (now - sent_date).days >= delay_days:
                stale.append((idx, e))

        if not stale:
            flash('No stale emails found (all within their stage delay or already replied).', 'info')
            return redirect(url_for('tracking.tracking_page'))

        engine = EmailPersonalizationEngine(get_api_key())
        sender = get_sender_info()
        gmail_service = get_gmail_service_for_user()
        sent_count = 0
        fail_count = 0

        for idx, e in stale:
            customer_id = e.get('customer_id', '')
            customer = next((c for c in customers if str(c.get('id')) == customer_id), None)
            if not customer:
                continue

            to_email = customer.get('contact_email', '')
            if not to_email:
                continue

            current_stage = int(e.get('pipeline_stage', 1)) if str(e.get('pipeline_stage', '1')).isdigit() else 1
            next_stage = min(current_stage + 1, max(PIPELINE_STAGES.keys()))
            stage_info = PIPELINE_STAGES.get(next_stage, {})
            attachment_files = stage_info.get('attachments', [])

            research = {
                'summary': customer.get('research_summary', ''),
                'industry': customer.get('tags', 'Manufacturing'),
                'pain_points': customer.get('pain_points', '')
            }
            delay_days = PIPELINE_STAGES.get(current_stage, {}).get('followup_days', followup_days)
            context = f"This is an automated follow-up. The previous email (Stage {current_stage}) was sent {delay_days}+ days ago with no reply. Now sending Stage {next_stage} ({stage_info.get('name', '')})."

            try:
                email_data = engine.generate_email(customer, research, next_stage, context)
                if not email_data:
                    fail_count += 1
                    continue

                subject = email_data.get('subject', '')
                body = email_data.get('body', '')
                msg_id, error = send_email_via_gmail(to_email, subject, body, attachment_files,
                                                      sender_name=sender['sender_name'],
                                                      sender_email=sender['sender_email'],
                                                      gmail_service=gmail_service)
                if error:
                    fail_count += 1
                    continue

                email_log = create_email_log(customer_id, customer, subject, body, next_stage,
                                             attachments=';'.join(attachment_files),
                                             status='sent', email_type='auto_followup',
                                             reviewed_by='auto_approved',
                                             gmail_msg_id=msg_id or '',
                                             confidence=email_data.get('confidence_score', ''))
                import uuid as _uuid
                email_log['email_id'] = f"AFU{int(time.time())}_{customer_id}_{_uuid.uuid4().hex[:4]}"
                email_log['reply_content_summary'] = f'Auto follow-up to {e.get("email_id", "")}'
                sheets.log_email(email_log)

                if 'status' in headers:
                    tracking_sheet.update_cell(idx, headers.index('status') + 1, 'followed_up')
                if 'next_action' in headers:
                    tracking_sheet.update_cell(idx, headers.index('next_action') + 1, f'Auto follow-up sent (Stage {next_stage})')

                sheets.update_customer(customer_id, {'pipeline_stage': next_stage})
                sent_count += 1
                time.sleep(1)
            except Exception as inner_e:
                logger.error(f"Auto follow-up failed for {to_email}: {inner_e}")
                fail_count += 1

        logger.info(f"Auto follow-up: {sent_count} sent, {fail_count} failed out of {len(stale)} stale")
        flash(f'Auto follow-up complete! Sent: {sent_count}, Failed: {fail_count} (from {len(stale)} stale emails)',
              'success' if fail_count == 0 else 'warning')

    except Exception as e:
        logger.error(f"Auto follow-up error: {e}")
        safe_flash_error(e, 'Tracking operation')

    return redirect(url_for('tracking.tracking_page'))


@tracking_bp.route('/tracking/send_scheduled')
@login_required
def send_scheduled():
    """Send all queued emails whose scheduled_date has arrived."""
    try:
        sheets = get_sheets()
        tracking_sheet = sheets.get_worksheet('Email_Tracking')
        emails = tracking_sheet.get_all_records()
        headers = tracking_sheet.row_values(1)
        customers = sheets.get_customers()
        today = datetime.now().strftime('%Y-%m-%d')

        scheduled = []
        for idx, e in enumerate(emails, start=2):
            sched_date = str(e.get('scheduled_date', '')).strip()
            if (e.get('status') == 'queued' and sched_date and sched_date <= today):
                scheduled.append((idx, e))

        if not scheduled:
            flash('No scheduled emails ready to send.', 'info')
            return redirect(url_for('tracking.tracking_page'))

        sender = get_sender_info()
        gmail_service = get_gmail_service_for_user()
        sent_count = 0
        fail_count = 0
        for idx, e in scheduled:
            customer_id = e.get('customer_id', '')
            customer = next((c for c in customers if str(c.get('id')) == customer_id), None)
            if not customer:
                fail_count += 1
                continue

            to_email = customer.get('contact_email', '')
            subject = e.get('subject', '')
            body = e.get('body', '')
            att_str = e.get('attachments', '')
            attachment_files = [a.strip() for a in str(att_str).split(';') if a.strip()] if att_str else []

            msg_id, error = send_email_via_gmail(to_email, subject, body, attachment_files,
                                                  sender_name=sender['sender_name'],
                                                  sender_email=sender['sender_email'],
                                                  gmail_service=gmail_service)
            if error:
                logger.warning(f"Scheduled send failed for {customer.get('company_name', '')}: {error}")
                fail_count += 1
                continue

            updates = {'status': 'sent', 'sent_time': datetime.now().strftime('%H:%M:%S'),
                       'gmail_msg_id': msg_id or ''}
            for key, val in updates.items():
                if key in headers:
                    tracking_sheet.update_cell(idx, headers.index(key) + 1, val)
            sent_count += 1
            time.sleep(1)

        flash(f'Scheduled send complete! Sent: {sent_count}, Failed: {fail_count}',
              'success' if fail_count == 0 else 'warning')

    except Exception as e:
        logger.error(f"Scheduled send error: {e}")
        safe_flash_error(e, 'Tracking operation')

    return redirect(url_for('tracking.tracking_page'))


@tracking_bp.route('/tracking/followup_queue')
@login_required
def followup_queue():
    """Show emails due for follow-up based on per-stage delays."""
    followup_days = get_user_config('followup_days', 3)
    try:
        sheets = get_sheets()
        tracking_sheet = sheets.get_worksheet('Email_Tracking')
        emails = tracking_sheet.get_all_records()
        customers = sheets.get_customers()

        queue = []
        now = datetime.now()
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
            stage_info = PIPELINE_STAGES.get(current_stage, {})
            delay_days = stage_info.get('followup_days', followup_days)

            if delay_days == 0:
                continue

            due_date = sent_date + timedelta(days=delay_days)
            days_overdue = (now - due_date).days

            if days_overdue >= 0:
                customer_id = e.get('customer_id', '')
                customer = next((c for c in customers if str(c.get('id')) == customer_id), None)
                next_stage = min(current_stage + 1, max(PIPELINE_STAGES.keys()))
                next_info = PIPELINE_STAGES.get(next_stage, {})

                queue.append({
                    'row_idx': idx,
                    'email_id': e.get('email_id', ''),
                    'customer_id': customer_id,
                    'company_name': customer.get('company_name', '-') if customer else '-',
                    'contact_email': e.get('contact_email', ''),
                    'subject': e.get('subject', '-'),
                    'sent_date': sent_date_str,
                    'current_stage': current_stage,
                    'current_stage_name': stage_info.get('name', ''),
                    'next_stage': next_stage,
                    'next_stage_name': next_info.get('name', ''),
                    'next_attachments': next_info.get('attachments', []),
                    'delay_days': delay_days,
                    'days_overdue': days_overdue,
                    'due_date': due_date.strftime('%Y-%m-%d'),
                })

        queue.sort(key=lambda x: x['days_overdue'], reverse=True)

        return render_template('tracking.html',
            active_page='tracking',
            emails=[],
            tab='followups',
            total_count=0,
            n_pending=0, n_queued=0, n_sent=0, n_replied=0,
            n_followups=len(queue),
            followup_queue=queue,
            pipeline_stages=PIPELINE_STAGES,
            page=1, total_pages=1,
        )

    except Exception as e:
        logger.error(f"Follow-up queue error: {e}")
        safe_flash_error(e, 'Load follow-up queue')
        return redirect(url_for('tracking.tracking_page'))


@tracking_bp.route('/tracking/snooze', methods=['POST'])
@login_required
def snooze_followup():
    """Snooze a follow-up by adding extra days to its sent_date effectively."""
    email_id = request.form.get('email_id', '')
    snooze_days = int(request.form.get('snooze_days', 3))
    redirect_to = request.form.get('redirect_to', 'followup_queue')
    company_name = request.form.get('company_name', '')
    followup_days = get_user_config('followup_days', 3)

    try:
        sheets = get_sheets()
        tracking_sheet = sheets.get_worksheet('Email_Tracking')
        records = tracking_sheet.get_all_records()
        headers = tracking_sheet.row_values(1)

        for idx, record in enumerate(records, start=2):
            if record.get('email_id') == email_id:
                old_date_str = record.get('sent_date', '')
                try:
                    old_date = datetime.strptime(old_date_str, '%Y-%m-%d')
                except ValueError:
                    flash(f'Cannot snooze: invalid sent_date for email {email_id}.', 'danger')
                    break
                new_date = (old_date + timedelta(days=snooze_days)).strftime('%Y-%m-%d')
                current_stage = int(record.get('pipeline_stage', 1)) if str(record.get('pipeline_stage', '1')).isdigit() else 1
                delay = PIPELINE_STAGES.get(current_stage, {}).get('followup_days', followup_days)
                new_due = (datetime.strptime(new_date, '%Y-%m-%d') + timedelta(days=delay)).strftime('%Y-%m-%d')

                if 'sent_date' in headers:
                    tracking_sheet.update_cell(idx, headers.index('sent_date') + 1, new_date)
                if 'next_action' in headers:
                    tracking_sheet.update_cell(idx, headers.index('next_action') + 1,
                                               f'Snoozed {snooze_days}d (original: {old_date_str})')

                label = f' for {company_name}' if company_name else ''
                logger.info(f"Snoozed follow-up {email_id} by {snooze_days} days")
                flash(f'Snoozed{label} by {snooze_days} days. New due date: {new_due}', 'info')
                break
        else:
            flash('Email not found.', 'danger')

    except Exception as e:
        logger.error(f"Snooze error: {e}")
        safe_flash_error(e, 'Tracking operation')

    if redirect_to == 'pipeline_view':
        return redirect(url_for('tracking.pipeline_view'))
    return redirect(url_for('tracking.followup_queue'))


@tracking_bp.route('/tracking/skip', methods=['POST'])
@login_required
def skip_followup():
    """Skip a follow-up - mark the email as 'skipped' so it won't appear in queue again."""
    email_id = request.form.get('email_id', '')
    redirect_to = request.form.get('redirect_to', 'followup_queue')

    try:
        sheets = get_sheets()
        tracking_sheet = sheets.get_worksheet('Email_Tracking')
        records = tracking_sheet.get_all_records()
        headers = tracking_sheet.row_values(1)

        for idx, record in enumerate(records, start=2):
            if record.get('email_id') == email_id:
                if 'status' in headers:
                    tracking_sheet.update_cell(idx, headers.index('status') + 1, 'skipped')
                if 'next_action' in headers:
                    tracking_sheet.update_cell(idx, headers.index('next_action') + 1, 'Follow-up skipped by user')

                logger.info(f"Skipped follow-up for {email_id}")
                flash('Follow-up skipped. This email will no longer appear in the queue.', 'warning')
                break
        else:
            flash('Email not found.', 'danger')

    except Exception as e:
        logger.error(f"Skip error: {e}")
        safe_flash_error(e, 'Tracking operation')

    if redirect_to == 'pipeline_view':
        return redirect(url_for('tracking.pipeline_view'))
    return redirect(url_for('tracking.followup_queue'))


@tracking_bp.route('/tracking/pipeline_view')
@login_required
def pipeline_view():
    """Show emails grouped by pipeline stage for easy stage-by-stage follow-up."""
    followup_days = get_user_config('followup_days', 3)
    try:
        sheets = get_sheets()
        sheet_emails = sheets.get_worksheet('Email_Tracking')
        emails = sheet_emails.get_all_records()
        customers = sheets.get_customers()
        customer_map = {str(c.get('id', '')): c for c in customers}
    except Exception as e:
        safe_flash_error(e, 'Load data')
        return redirect(url_for('tracking.tracking_page'))

    now = datetime.now()
    stage_filter = request.args.get('stage', '')

    stage_groups = {}
    for stage_num in sorted(PIPELINE_STAGES.keys()):
        stage_groups[stage_num] = {
            'info': PIPELINE_STAGES[stage_num],
            'emails': [],
            'total': 0,
            'replied': 0,
            'needs_action': 0,
            'awaiting': 0,
            'followed_up': 0,
        }

    for e in emails:
        p_stage = str(e.get('pipeline_stage', '1'))
        stage_num = int(p_stage) if p_stage.isdigit() else 1
        if stage_num not in stage_groups:
            stage_num = 1

        status = e.get('status', '')
        replied = e.get('replied', 'no')
        reply_summary = str(e.get('reply_content_summary', ''))
        req_type = ''
        if reply_summary.startswith('[') and ']' in reply_summary:
            req_type = reply_summary[1:reply_summary.index(']')]

        customer = customer_map.get(str(e.get('customer_id', '')), {})
        detected = str(e.get('detected_stage', ''))
        detected_info = PIPELINE_STAGES.get(int(detected), {}) if detected.isdigit() else {}

        days_since = ''
        is_overdue = False
        sent_date_str = e.get('sent_date', '')
        if sent_date_str:
            try:
                sent_date = datetime.strptime(sent_date_str, '%Y-%m-%d')
                days_since = (now - sent_date).days
                delay = PIPELINE_STAGES.get(stage_num, {}).get('followup_days', followup_days)
                if delay > 0 and days_since >= delay and status == 'sent' and replied != 'yes':
                    is_overdue = True
            except ValueError:
                pass

        entry = {
            'email_id': e.get('email_id', ''),
            'customer_id': e.get('customer_id', ''),
            'company_name': e.get('company_name', customer.get('company_name', '-')),
            'contact_email': e.get('contact_email', ''),
            'subject': e.get('subject', ''),
            'sent_date': sent_date_str,
            'status': status,
            'replied': replied,
            'request_type': req_type,
            'reply_summary': reply_summary[:80] if reply_summary else '',
            'detected_stage': detected,
            'detected_stage_name': detected_info.get('name', ''),
            'detected_attachments': detected_info.get('attachments', []),
            'engagement': customer.get('engagement_level', ''),
            'days_since': days_since,
            'is_overdue': is_overdue,
        }

        sg = stage_groups[stage_num]
        sg['emails'].append(entry)
        sg['total'] += 1
        if replied == 'yes':
            sg['replied'] += 1
            if status == 'replied':
                sg['needs_action'] += 1
        elif status == 'sent':
            sg['awaiting'] += 1
        if status == 'followed_up':
            sg['followed_up'] += 1

    for sg in stage_groups.values():
        sg['emails'].sort(key=lambda x: (
            0 if (x['replied'] == 'yes' and x['status'] == 'replied') else 1,
            0 if x['is_overdue'] else 1,
            x.get('sent_date', '') or '0000',
        ))

    total_count = len(emails)
    n_pending = len([e for e in emails if e.get('reviewed_by') == 'pending_review'])
    n_queued = len([e for e in emails if e.get('status') == 'queued'])
    n_sent = len([e for e in emails if e.get('status') == 'sent'])
    n_replied = len([e for e in emails if e.get('replied') == 'yes'])
    n_followups = 0
    for e in emails:
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
        delay = PIPELINE_STAGES.get(current_stage, {}).get('followup_days', followup_days)
        if delay > 0 and (now - sent_date).days >= delay:
            n_followups += 1

    return render_template('tracking.html',
        active_page='tracking',
        emails=[],
        tab='pipeline',
        total_count=total_count,
        n_pending=n_pending, n_queued=n_queued, n_sent=n_sent, n_replied=n_replied,
        n_followups=n_followups,
        followup_queue=[],
        pipeline_stages=PIPELINE_STAGES,
        stage_groups=stage_groups,
        stage_filter=stage_filter,
        page=1, total_pages=1,
    )


@tracking_bp.route('/tracking/export-csv')
@login_required
def export_tracking_csv():
    """Export email tracking data as CSV."""
    try:
        sheets = get_sheets()
        tracking_sheet = sheets.get_worksheet('Email_Tracking')
        emails = tracking_sheet.get_all_records()

        output = io.StringIO()
        if emails:
            writer = csv.DictWriter(output, fieldnames=emails[0].keys())
            writer.writeheader()
            writer.writerows(emails)
        else:
            output.write('No email tracking data found.\n')

        return Response(output.getvalue(), mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=email_tracking_export.csv'})
    except Exception as e:
        flash(f'Export failed: {e}', 'danger')
        return redirect(url_for('tracking.tracking_page'))
