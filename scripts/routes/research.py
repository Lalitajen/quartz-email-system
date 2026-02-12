"""Research routes."""

import time
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app_core import (login_required, get_sheets, cached_get_customers, invalidate_cache,
                      AIResearchEngine, API_KEY, RESEARCH_DELAY, MAX_RESEARCH_PER_RUN, logger)

research_bp = Blueprint('research', __name__)


@research_bp.route('/research')
@login_required
def research_page():
    try:
        customers = cached_get_customers()
    except Exception as e:
        return render_template('research.html', active_page='research', error=str(e),
                               customers=[], selected=None, selected_id='')

    selected_id = request.args.get('id', '')
    selected = next((c for c in customers if str(c.get('id')) == selected_id), None) if selected_id else None

    return render_template('research.html',
        active_page='research',
        customers=customers,
        selected=selected,
        selected_id=selected_id,
    )


@research_bp.route('/research/run', methods=['POST'])
@login_required
def run_research():
    customer_id = request.form.get('customer_id', '')
    try:
        sheets = get_sheets()
        customers = sheets.get_customers()
        customer = next((c for c in customers if str(c.get('id')) == customer_id), None)

        if not customer:
            flash('Customer not found.', 'danger')
            return redirect(url_for('research.research_page'))

        engine = AIResearchEngine(API_KEY)
        research = engine.research_company(customer.get('company_name', ''), customer.get('company_website', ''))

        sheets.update_customer(customer_id, {
            'research_status': 'completed',
            'research_summary': research.get('summary', ''),
            'pain_points': research.get('pain_points', '')
        })
        invalidate_cache()
        logger.info(f"Research completed for {customer.get('company_name')}")
        flash(f'Research completed for {customer.get("company_name")}!', 'success')
    except Exception as e:
        logger.error(f"Research failed for {customer_id}: {e}")
        flash(f'Research failed: {e}', 'danger')
    return redirect(url_for('research.research_page', id=customer_id))


@research_bp.route('/research/run-all', methods=['POST'])
@login_required
def run_research_all():
    try:
        sheets = get_sheets()
        customers = sheets.get_customers()
        pending = [c for c in customers if c.get('research_status') == 'pending']

        if not pending:
            flash('No pending research found.', 'info')
            return redirect(url_for('research.research_page'))

        engine = AIResearchEngine(API_KEY)
        count = 0
        for customer in pending[:MAX_RESEARCH_PER_RUN]:
            research = engine.research_company(customer.get('company_name', ''), customer.get('company_website', ''))
            sheets.update_customer(str(customer.get('id', '')), {
                'research_status': 'completed',
                'research_summary': research.get('summary', ''),
                'pain_points': research.get('pain_points', '')
            })
            count += 1
            time.sleep(RESEARCH_DELAY)

        invalidate_cache()
        logger.info(f"Batch research completed for {count} customers")
        flash(f'Research completed for {count} customers!', 'success')
    except Exception as e:
        logger.error(f"Batch research failed: {e}")
        flash(f'Batch research failed: {e}', 'danger')
    return redirect(url_for('research.research_page'))
