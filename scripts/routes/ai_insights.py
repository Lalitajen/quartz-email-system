"""AI Insights routes - Smart recommendations, upsell intelligence, and prospect discovery."""

import json
import time
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app_core import (login_required, get_sheets, cached_get_customers, invalidate_cache,
                      PIPELINE_STAGES, get_api_key, logger)

ai_insights_bp = Blueprint('ai_insights', __name__)


@ai_insights_bp.route('/ai-insights')
@login_required
def insights_page():
    try:
        customers = cached_get_customers()
        sheets = get_sheets()
        sheet_emails = sheets.get_worksheet('Email_Tracking')
        emails = sheet_emails.get_all_records()
    except Exception as e:
        return render_template('ai_insights.html', active_page='ai_insights',
                               error=str(e), hot_leads=[], upsell_ready=[],
                               stale_customers=[], action_items=[],
                               pipeline_stages=PIPELINE_STAGES,
                               total_analyzed=0, total_customers=0,
                               discovered_prospects=[], discover_keyword='')

    # --- HOT LEADS needing attention ---
    hot_leads = [c for c in customers
                 if str(c.get('engagement_level', '')).upper() == 'HOT'
                 or str(c.get('buying_intent', '')).lower() == 'high']
    hot_leads.sort(key=lambda c: int(c.get('urgency_score', 0) or 0), reverse=True)

    # --- UPSELL READY ---
    upsell_ready = []
    max_stage = max(PIPELINE_STAGES.keys()) if PIPELINE_STAGES else 10
    for c in customers:
        stage = int(c.get('pipeline_stage', 1) or 1) if str(c.get('pipeline_stage', '1')).isdigit() else 1
        intent = str(c.get('buying_intent', '')).lower()
        engagement = str(c.get('engagement_level', '')).upper()
        if stage < max_stage - 1 and intent in ('high', 'medium') and engagement in ('HOT', 'WARM'):
            next_stage = stage + 1
            next_info = PIPELINE_STAGES.get(next_stage, {})
            upsell_ready.append({
                'customer': c,
                'current_stage': stage,
                'current_stage_name': PIPELINE_STAGES.get(stage, {}).get('name', str(stage)),
                'next_stage': next_stage,
                'next_stage_name': next_info.get('name', str(next_stage)),
                'next_attachments': next_info.get('attachments', []),
                'reason': c.get('next_action', 'Ready for next stage'),
            })
    upsell_ready.sort(key=lambda x: int(x['customer'].get('urgency_score', 0) or 0), reverse=True)

    # --- STALE CUSTOMERS ---
    stale_customers = []
    today = datetime.now()
    for c in customers:
        stage = int(c.get('pipeline_stage', 1) or 1) if str(c.get('pipeline_stage', '1')).isdigit() else 1
        if stage == 10:
            continue
        last_contact = c.get('last_contact_date', '')
        if last_contact:
            try:
                last_dt = datetime.strptime(str(last_contact), '%Y-%m-%d')
                days_ago = (today - last_dt).days
                if days_ago >= 14:
                    stale_customers.append({
                        'customer': c,
                        'days_since_contact': days_ago,
                    })
            except ValueError:
                pass
    stale_customers.sort(key=lambda x: x['days_since_contact'], reverse=True)

    # --- PRIORITIZED ACTION LIST ---
    action_items = []
    for c in hot_leads[:5]:
        action_items.append({
            'priority': 'high',
            'icon': 'fire',
            'color': 'danger',
            'customer': c,
            'action': c.get('next_action', 'Follow up immediately'),
            'reason': f'HOT lead, urgency {c.get("urgency_score", "?")}/10',
        })
    for u in upsell_ready[:5]:
        action_items.append({
            'priority': 'medium',
            'icon': 'arrow-up-circle',
            'color': 'warning',
            'customer': u['customer'],
            'action': f'Move to Stage {u["next_stage"]} ({u["next_stage_name"]})',
            'reason': u['reason'],
        })
    for s in stale_customers[:5]:
        action_items.append({
            'priority': 'low',
            'icon': 'clock-history',
            'color': 'secondary',
            'customer': s['customer'],
            'action': 'Re-engage with new value proposition',
            'reason': f'No contact for {s["days_since_contact"]} days',
        })

    discovered_prospects = session.get('discovered_prospects', [])
    discover_keyword = session.get('discover_keyword', '')

    return render_template('ai_insights.html',
        active_page='ai_insights',
        hot_leads=hot_leads[:10],
        upsell_ready=upsell_ready[:10],
        stale_customers=stale_customers[:10],
        action_items=action_items,
        pipeline_stages=PIPELINE_STAGES,
        total_analyzed=len([c for c in customers if c.get('last_analyzed')]),
        total_customers=len(customers),
        discovered_prospects=discovered_prospects,
        discover_keyword=discover_keyword,
    )


@ai_insights_bp.route('/ai-insights/discover', methods=['POST'])
@login_required
def discover_prospects():
    """AI-powered prospect discovery by industry keyword."""
    keyword = request.form.get('keyword', '').strip()
    if not keyword:
        flash('Please enter an industry keyword.', 'warning')
        return redirect(url_for('ai_insights.insights_page'))

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=get_api_key())

        prompt = f"""You are a B2B sales intelligence assistant for a high-purity quartz mining and export company (Lorh La Seng Commercial).

The user wants to find potential B2B customers in this industry/keyword area: "{keyword}"

Generate a list of 10 realistic types of companies that would be potential customers for high-purity quartz (SiO2 99.5%+).
For each, provide:
1. company_type: Type of company (e.g., "Semiconductor Wafer Manufacturer")
2. example_name: A realistic example company name
3. typical_website: A plausible domain (e.g., "example-semi.com")
4. contact_department: Best department to contact (e.g., "Procurement", "R&D")
5. reason: Why they need high-purity quartz (1 sentence)
6. estimated_size: Small/Medium/Large

Format as a JSON array of objects. Return ONLY the JSON array, no other text."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        if '[' in response_text and ']' in response_text:
            json_start = response_text.index('[')
            json_end = response_text.rindex(']') + 1
            prospects = json.loads(response_text[json_start:json_end])
        else:
            prospects = []
            flash('AI could not generate structured prospects. Try a different keyword.', 'warning')

        session['discovered_prospects'] = prospects
        session['discover_keyword'] = keyword

        if prospects:
            flash(f'Found {len(prospects)} potential prospect types for "{keyword}"!', 'success')
        logger.info(f"Prospect discovery for '{keyword}': {len(prospects)} results")

    except Exception as e:
        logger.error(f"Prospect discovery failed: {e}")
        flash(f'Discovery failed: {e}', 'danger')

    return redirect(url_for('ai_insights.insights_page'))


@ai_insights_bp.route('/ai-insights/import-prospects', methods=['POST'])
@login_required
def import_prospects():
    """Import selected AI-discovered prospects to customer list."""
    prospects = session.get('discovered_prospects', [])
    selected_indices = request.form.getlist('prospect_idx')

    if not selected_indices:
        flash('No prospects selected for import.', 'warning')
        return redirect(url_for('ai_insights.insights_page'))

    try:
        sheets = get_sheets()
        sheet = sheets.get_worksheet('Customers')
        headers = sheet.row_values(1)
        count = 0

        for idx_str in selected_indices:
            idx = int(idx_str)
            if idx < len(prospects):
                p = prospects[idx]
                customer_id = f"CUST{int(time.time())}_{count}"
                row_data = {
                    'id': customer_id,
                    'company_name': p.get('example_name', p.get('company_type', '')),
                    'company_email': '',
                    'company_website': f"https://{p.get('typical_website', '')}",
                    'contact_name': '',
                    'contact_email': '',
                    'contact_department': p.get('contact_department', ''),
                    'pipeline_stage': '1',
                    'tags': f"ai-discovered, {p.get('company_type', '')}",
                    'research_status': 'pending',
                    'research_summary': p.get('reason', ''),
                    'pain_points': '',
                    'last_contact_date': datetime.now().strftime('%Y-%m-%d'),
                    'response_status': 'no_contact',
                    'notes': f"AI-discovered prospect for: {session.get('discover_keyword', '')}",
                }
                sheet.append_row([str(row_data.get(h, '')) for h in headers])
                count += 1
                time.sleep(0.5)

        invalidate_cache()
        session.pop('discovered_prospects', None)
        session.pop('discover_keyword', None)
        logger.info(f"Imported {count} AI-discovered prospects")
        flash(f'Imported {count} prospects to customer list!', 'success')
    except Exception as e:
        logger.error(f"Prospect import failed: {e}")
        flash(f'Import failed: {e}', 'danger')

    return redirect(url_for('customers.customers_page'))
