"""Dashboard route."""

import json
from collections import Counter
from datetime import datetime, timedelta
from flask import Blueprint, render_template
from app_core import login_required, cached_get_customers, get_sheets, PIPELINE_STAGES, get_user_config

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def dashboard():
    max_emails = get_user_config('max_emails_per_day', 50)
    try:
        sheets = get_sheets()
        customers = cached_get_customers()
        sheet_emails = sheets.get_worksheet('Email_Tracking')
        emails = sheet_emails.get_all_records()
    except Exception as e:
        return render_template('dashboard.html', active_page='dashboard', error=str(e),
                               total_customers=0, emails_sent=0, response_rate=0, hot=0,
                               pending_reviews=0, researched=0, emails_queued=0,
                               warm=0, interested=0, cold=0, unsegmented=0,
                               pipeline_stages=PIPELINE_STAGES, stage_counts={},
                               today_sent=0, today_replies=0, max_emails_per_day=max_emails,
                               now=datetime.now().strftime('%B %d, %Y %H:%M'),
                               high_intent_count=0, upsell_candidates=0, analyzed_count=0)

    total_customers = len(customers)
    emails_sent = len([e for e in emails if e.get('status') == 'sent'])
    emails_queued = len([e for e in emails if e.get('status') == 'queued'])
    replies = len([e for e in emails if e.get('replied') == 'yes'])
    response_rate = round(replies / emails_sent * 100, 1) if emails_sent else 0
    pending_reviews = len([e for e in emails if e.get('reviewed_by') == 'pending_review'])
    researched = len([c for c in customers if c.get('research_status') == 'completed'])

    hot = len([c for c in customers if str(c.get('engagement_level', '')).upper() == 'HOT'])
    warm = len([c for c in customers if str(c.get('engagement_level', '')).upper() == 'WARM'])
    interested = len([c for c in customers if str(c.get('engagement_level', '')).upper() == 'INTERESTED'])
    cold = len([c for c in customers if str(c.get('engagement_level', '')).upper() == 'COLD'])
    unresponsive = len([c for c in customers if str(c.get('engagement_level', '')).upper() == 'UNRESPONSIVE'])
    unsegmented = total_customers - hot - warm - interested - cold - unresponsive

    high_intent_count = len([c for c in customers if str(c.get('buying_intent', '')).lower() == 'high'])
    upsell_candidates = len([c for c in customers
        if str(c.get('pipeline_stage', '1')).isdigit()
        and int(c.get('pipeline_stage', 1)) < 9
        and str(c.get('buying_intent', '')).lower() in ('high', 'medium')
        and str(c.get('engagement_level', '')).upper() in ('HOT', 'WARM')])
    analyzed_count = len([c for c in customers if c.get('last_analyzed')])

    stage_counts = {}
    for stage_num in PIPELINE_STAGES:
        stage_counts[stage_num] = len([c for c in customers if str(c.get('pipeline_stage')) == str(stage_num)])

    today = datetime.now().strftime('%Y-%m-%d')
    today_sent = len([e for e in emails if e.get('sent_date') == today and e.get('status') == 'sent'])
    today_replies = len([e for e in emails if e.get('reply_date') == today])

    daily_sent = Counter()
    daily_replies = Counter()
    for e in emails:
        sd = e.get('sent_date', '')
        if sd and e.get('status') == 'sent':
            daily_sent[sd] += 1
        rd = e.get('reply_date', '')
        if rd:
            daily_replies[rd] += 1

    chart_days = 14
    date_labels = []
    sent_data = []
    reply_data = []
    for i in range(chart_days - 1, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        date_labels.append(d[-5:])
        sent_data.append(daily_sent.get(d, 0))
        reply_data.append(daily_replies.get(d, 0))

    return render_template('dashboard.html',
        active_page='dashboard',
        total_customers=total_customers,
        emails_sent=emails_sent,
        emails_queued=emails_queued,
        response_rate=response_rate,
        hot=hot, warm=warm, interested=interested, cold=cold,
        unsegmented=unsegmented,
        pending_reviews=pending_reviews,
        researched=researched,
        pipeline_stages=PIPELINE_STAGES,
        stage_counts=stage_counts,
        today_sent=today_sent,
        today_replies=today_replies,
        max_emails_per_day=max_emails,
        now=datetime.now().strftime('%B %d, %Y %H:%M'),
        chart_labels=json.dumps(date_labels),
        chart_sent=json.dumps(sent_data),
        chart_replies=json.dumps(reply_data),
        high_intent_count=high_intent_count,
        upsell_candidates=upsell_candidates,
        analyzed_count=analyzed_count,
    )
