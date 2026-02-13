"""Customer management routes."""

import csv
import io
import time
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from app_core import (login_required, get_sheets, invalidate_cache, cached_get_customers,
                      ENGAGEMENT_COLORS, PIPELINE_STAGES, AIResearchEngine, get_api_key,
                      is_valid_email, get_segmentation_engine, logger, safe_flash_error)

customers_bp = Blueprint('customers', __name__)

PER_PAGE = 25


@customers_bp.route('/customers')
@login_required
def customers_page():
    try:
        customers = cached_get_customers()
    except Exception as e:
        return render_template('customers.html', active_page='customers', error=str(e),
                               customers=[], total_count=0, filter_engagement='',
                               filter_stage='', eng_counts={}, engagement_colors=ENGAGEMENT_COLORS,
                               page=1, total_pages=1)

    filter_engagement = request.args.get('engagement', '')
    filter_stage = request.args.get('stage', '')
    page = request.args.get('page', 1, type=int)

    filtered = customers
    if filter_engagement:
        filtered = [c for c in filtered if str(c.get('engagement_level', '')).upper() == filter_engagement.upper()]
    if filter_stage:
        filtered = [c for c in filtered if str(c.get('pipeline_stage')) == filter_stage]

    eng_counts = {}
    for c in customers:
        lvl = str(c.get('engagement_level', 'N/A')).upper()
        eng_counts[lvl] = eng_counts.get(lvl, 0) + 1

    total_count = len(filtered)
    total_pages = max(1, (total_count + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * PER_PAGE
    paginated = filtered[start:start + PER_PAGE]

    return render_template('customers.html',
        active_page='customers',
        customers=paginated,
        total_count=len(customers),
        filter_engagement=filter_engagement,
        filter_stage=filter_stage,
        eng_counts=eng_counts,
        engagement_colors=ENGAGEMENT_COLORS,
        page=page,
        total_pages=total_pages,
    )


@customers_bp.route('/customers/csv-template')
@login_required
def csv_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['company_name', 'contact_name', 'contact_email', 'company_website',
                     'company_email', 'contact_department', 'tags'])
    writer.writerow(['ABC Semiconductors', 'John Smith', 'john@abcsemi.com',
                     'https://abcsemi.com', 'info@abcsemi.com', 'Purchasing', 'semiconductor,hot'])
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=customer_import_template.csv'})


@customers_bp.route('/customers/export-csv')
@login_required
def export_csv():
    """Export all customers as CSV."""
    try:
        customers = cached_get_customers()
        output = io.StringIO()
        if customers:
            fields = ['id', 'company_name', 'contact_name', 'contact_email', 'company_email',
                       'company_website', 'contact_department', 'pipeline_stage', 'engagement_level',
                       'tags', 'research_status', 'research_summary', 'last_contact_date']
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(customers)
        return Response(output.getvalue(), mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=customers_export.csv'})
    except Exception as e:
        flash(f'Export failed: {e}', 'danger')
        return redirect(url_for('customers.customers_page'))


@customers_bp.route('/customers/import-csv', methods=['POST'])
@login_required
def import_csv():
    if 'csv_file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('customers.customers_page'))

    file = request.files['csv_file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('customers.customers_page'))

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 2 * 1024 * 1024:
        flash('CSV file too large (max 2 MB).', 'danger')
        return redirect(url_for('customers.customers_page'))

    try:
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        sheets = get_sheets()
        sheet = sheets.get_worksheet('Customers')
        headers = sheet.row_values(1)

        existing = sheets.get_customers()
        existing_emails = {c.get('contact_email', '').lower() for c in existing if c.get('contact_email')}
        existing_companies = {c.get('company_name', '').lower() for c in existing if c.get('company_name')}

        count = 0
        skipped = 0
        duplicates = 0
        for row in reader:
            if not row.get('company_name') or not row.get('contact_email'):
                skipped += 1
                continue
            if not is_valid_email(row['contact_email']):
                skipped += 1
                continue
            row_email = row['contact_email'].strip().lower()
            row_company = row['company_name'].strip().lower()
            if row_email in existing_emails or row_company in existing_companies:
                duplicates += 1
                continue
            existing_emails.add(row_email)
            existing_companies.add(row_company)
            customer_id = f"CUST{int(time.time())}_{count}"
            row_data = {
                'id': customer_id,
                'company_name': row.get('company_name', ''),
                'company_email': row.get('company_email', ''),
                'company_website': row.get('company_website', ''),
                'contact_name': row.get('contact_name', ''),
                'contact_email': row.get('contact_email', ''),
                'contact_department': row.get('contact_department', ''),
                'pipeline_stage': row.get('pipeline_stage', '1'),
                'tags': row.get('tags', ''),
                'research_status': 'pending',
                'research_summary': '', 'pain_points': '',
                'last_contact_date': datetime.now().strftime('%Y-%m-%d'),
                'response_status': 'no_contact', 'notes': ''
            }
            sheet.append_row([row_data.get(h, '') for h in headers])
            count += 1
            time.sleep(0.5)

        invalidate_cache()
        logger.info(f"Imported {count} customers from CSV, skipped {skipped}, duplicates {duplicates}")
        msg = f'Successfully imported {count} customers from CSV!'
        if duplicates:
            msg += f' ({duplicates} duplicates skipped)'
        if skipped:
            msg += f' ({skipped} rows skipped - missing or invalid data)'
        flash(msg, 'success' if (skipped == 0 and duplicates == 0) else 'warning')
    except Exception as e:
        logger.error(f"CSV import failed: {e}")
        flash(f'Import failed: {e}', 'danger')

    return redirect(url_for('customers.customers_page'))


@customers_bp.route('/customers/add', methods=['POST'])
@login_required
def add_customer():
    contact_email = request.form.get('contact_email', '').strip()
    if not contact_email or not is_valid_email(contact_email):
        flash(f'Invalid email address: "{contact_email}". Please enter a valid email.', 'danger')
        return redirect(url_for('customers.customers_page'))

    try:
        sheets = get_sheets()
        sheet = sheets.get_worksheet('Customers')
        headers = sheet.row_values(1)

        existing = sheets.get_customers()
        company_name = request.form.get('company_name', '').strip()
        dup_email = [c for c in existing if c.get('contact_email', '').lower() == contact_email.lower()]
        dup_company = [c for c in existing if company_name and c.get('company_name', '').lower() == company_name.lower()]

        if dup_email:
            dup = dup_email[0]
            flash(f'Duplicate detected: email "{contact_email}" already exists for '
                  f'"{dup.get("company_name", "")}" (ID: {dup.get("id", "")}).', 'warning')
            return redirect(url_for('customers.customers_page'))
        if dup_company:
            dup = dup_company[0]
            flash(f'Duplicate detected: company "{company_name}" already exists '
                  f'(ID: {dup.get("id", "")}, email: {dup.get("contact_email", "")}).', 'warning')
            return redirect(url_for('customers.customers_page'))

        customer_id = f"CUST{int(time.time())}"
        row_data = {
            'id': customer_id,
            'company_name': request.form.get('company_name', ''),
            'company_email': request.form.get('company_email', ''),
            'company_website': request.form.get('company_website', ''),
            'contact_name': request.form.get('contact_name', ''),
            'contact_email': request.form.get('contact_email', ''),
            'contact_department': request.form.get('department', ''),
            'pipeline_stage': '1',
            'tags': request.form.get('tags', ''),
            'research_status': 'pending', 'research_summary': '', 'pain_points': '',
            'last_contact_date': datetime.now().strftime('%Y-%m-%d'),
            'response_status': 'no_contact', 'notes': ''
        }
        sheet.append_row([row_data.get(h, '') for h in headers])
        invalidate_cache()
        logger.info(f"Added customer: {row_data['company_name']}")

        auto_research = request.form.get('auto_research') == 'on'
        if auto_research and row_data['company_website']:
            try:
                engine = AIResearchEngine(get_api_key())
                research = engine.research_company(row_data['company_name'], row_data['company_website'])
                sheets.update_customer(customer_id, {
                    'research_status': 'completed',
                    'research_summary': research.get('summary', ''),
                    'pain_points': research.get('pain_points', '')
                })
                invalidate_cache()
                flash(f'Customer {row_data["company_name"]} added and researched!', 'success')
            except Exception as re:
                logger.warning(f"Auto-research failed for {row_data['company_name']}: {re}")
                flash(f'Customer added but research failed: {re}', 'warning')
        else:
            flash(f'Customer {row_data["company_name"]} added!', 'success')
    except Exception as e:
        safe_flash_error(e, 'Add customer')

    return redirect(url_for('customers.customers_page'))


@customers_bp.route('/customers/<customer_id>')
@login_required
def customer_detail(customer_id):
    try:
        sheets = get_sheets()
        customers = sheets.get_customers()
        customer = next((c for c in customers if str(c.get('id')) == customer_id), None)

        if not customer:
            flash('Customer not found.', 'danger')
            return redirect(url_for('customers.customers_page'))

        sheet_emails = sheets.get_worksheet('Email_Tracking')
        all_emails = sheet_emails.get_all_records()
        customer_emails = [e for e in all_emails
                          if str(e.get('customer_id')) == customer_id
                          or e.get('contact_email') == customer.get('contact_email', '')]
        customer_emails.sort(key=lambda e: e.get('sent_date', ''), reverse=True)

        this_email = customer.get('contact_email', '').lower()
        this_company = customer.get('company_name', '').lower()
        duplicates = []
        for c in customers:
            if str(c.get('id')) == customer_id:
                continue
            match_reasons = []
            if this_email and c.get('contact_email', '').lower() == this_email:
                match_reasons.append('same email')
            if this_company and c.get('company_name', '').lower() == this_company:
                match_reasons.append('same company name')
            if match_reasons:
                duplicates.append({'customer': c, 'reasons': match_reasons})

        return render_template('customer_detail.html',
            active_page='customers',
            customer=customer,
            emails=customer_emails,
            pipeline_stages=PIPELINE_STAGES,
            duplicates=duplicates,
        )
    except Exception as e:
        safe_flash_error(e, 'Load customer')
        return redirect(url_for('customers.customers_page'))


@customers_bp.route('/customers/<customer_id>/edit', methods=['POST'])
@login_required
def edit_customer(customer_id):
    """Update customer fields."""
    try:
        sheets = get_sheets()
        updates = {}
        for field in ['company_name', 'contact_name', 'contact_email', 'company_email',
                       'company_website', 'contact_department', 'tags', 'pipeline_stage',
                       'engagement_level', 'notes']:
            val = request.form.get(field)
            if val is not None:
                updates[field] = val.strip()

        if 'contact_email' in updates and not is_valid_email(updates['contact_email']):
            flash(f'Invalid email address: "{updates["contact_email"]}"', 'danger')
            return redirect(url_for('customers.customer_detail', customer_id=customer_id))

        sheets.update_customer(customer_id, updates)
        invalidate_cache()
        logger.info(f"Updated customer {customer_id}")
        flash('Customer updated successfully!', 'success')
    except Exception as e:
        safe_flash_error(e, 'Update customer')

    return redirect(url_for('customers.customer_detail', customer_id=customer_id))


@customers_bp.route('/customers/<customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    """Delete a customer from the spreadsheet."""
    try:
        sheets = get_sheets()
        sheet = sheets.get_worksheet('Customers')
        records = sheet.get_all_records()

        for idx, record in enumerate(records, start=2):
            if str(record.get('id')) == customer_id:
                try:
                    email_sheet = sheets.get_worksheet('Email_Tracking')
                    all_emails = email_sheet.get_all_records()
                    linked = [e for e in all_emails
                              if str(e.get('customer_id')) == customer_id
                              or e.get('contact_email', '').lower() == record.get('contact_email', '').lower()]
                    linked_count = len(linked)
                except Exception:
                    linked_count = 0

                sheet.delete_rows(idx)
                invalidate_cache()
                logger.info(f"Deleted customer {customer_id} (had {linked_count} email records)")
                msg = f'Customer "{record.get("company_name", customer_id)}" deleted successfully!'
                if linked_count:
                    msg += f' Note: {linked_count} email record(s) in tracking still reference this customer.'
                flash(msg, 'success' if linked_count == 0 else 'warning')
                return redirect(url_for('customers.customers_page'))

        flash('Customer not found.', 'danger')
    except Exception as e:
        safe_flash_error(e, 'Delete customer')

    return redirect(url_for('customers.customers_page'))


@customers_bp.route('/customers/<customer_id>/analyze', methods=['POST'])
@login_required
def analyze_customer(customer_id):
    """Run AI engagement analysis on a single customer."""
    try:
        sheets = get_sheets()
        customers = sheets.get_customers()
        customer = next((c for c in customers if str(c.get('id')) == customer_id), None)
        if not customer:
            flash('Customer not found.', 'danger')
            return redirect(url_for('customers.customers_page'))

        sheet_emails = sheets.get_worksheet('Email_Tracking')
        all_emails = sheet_emails.get_all_records()
        customer_emails = [e for e in all_emails
                          if str(e.get('customer_id')) == customer_id
                          or e.get('contact_email') == customer.get('contact_email', '')]

        engine = get_segmentation_engine()
        analysis = engine.analyze_customer_engagement(customer, customer_emails)

        updates = {
            'engagement_level': str(analysis.get('engagement_level', '')),
            'buying_intent': str(analysis.get('buying_intent', '')),
            'urgency_score': str(analysis.get('urgency_score', '')),
            'next_action': str(analysis.get('next_action', '')),
            'last_analyzed': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        if analysis.get('pain_points'):
            updates['pain_points'] = str(analysis.get('pain_points', ''))

        sheets.update_customer(customer_id, updates)
        invalidate_cache()
        logger.info(f"AI analysis for {customer.get('company_name')}: {analysis.get('engagement_level')}, intent={analysis.get('buying_intent')}")
        flash(f'AI Analysis complete for {customer.get("company_name")}! '
              f'Engagement: {analysis.get("engagement_level")}, '
              f'Intent: {analysis.get("buying_intent")}, '
              f'Urgency: {analysis.get("urgency_score")}/10', 'success')
    except Exception as e:
        logger.error(f"AI analysis failed for {customer_id}: {e}")
        flash(f'AI analysis failed: {e}', 'danger')
    return redirect(url_for('customers.customer_detail', customer_id=customer_id))


@customers_bp.route('/customers/analyze-all', methods=['POST'])
@login_required
def analyze_all_customers():
    """Batch AI analysis on customers (max 10 per run)."""
    try:
        sheets = get_sheets()
        customers = sheets.get_customers()
        sheet_emails = sheets.get_worksheet('Email_Tracking')
        all_emails = sheet_emails.get_all_records()
        engine = get_segmentation_engine()

        count = 0
        max_batch = 10
        for customer in customers[:max_batch]:
            customer_id = str(customer.get('id', ''))
            customer_emails = [e for e in all_emails
                              if str(e.get('customer_id')) == customer_id
                              or e.get('contact_email') == customer.get('contact_email', '')]

            analysis = engine.analyze_customer_engagement(customer, customer_emails)
            sheets.update_customer(customer_id, {
                'engagement_level': str(analysis.get('engagement_level', '')),
                'buying_intent': str(analysis.get('buying_intent', '')),
                'urgency_score': str(analysis.get('urgency_score', '')),
                'next_action': str(analysis.get('next_action', '')),
                'last_analyzed': datetime.now().strftime('%Y-%m-%d %H:%M'),
            })
            count += 1
            time.sleep(1)

        invalidate_cache()
        logger.info(f"Batch AI analysis completed for {count} customers")
        flash(f'AI Analysis completed for {count} customers!', 'success')
    except Exception as e:
        logger.error(f"Batch AI analysis failed: {e}")
        flash(f'Batch analysis failed: {e}', 'danger')
    return redirect(url_for('customers.customers_page'))
