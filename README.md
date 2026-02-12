# Quartz Email Outreach System v3.0

Automated B2B email outreach system for quartz mining & export. Features AI-powered research, personalized email generation, Gmail integration, and a full web dashboard.

---

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
cp config/.env.template config/.env
# Edit config/.env with your API keys

# 4. Run the web app
python scripts/web_app.py
# Open http://localhost:5000 (login: admin / quartz2024)
```

---

## Project Structure

```
quartz-email-system/
├── scripts/
│   ├── web_app.py                 # Flask app factory (entry point)
│   ├── app_core.py                # Shared config, auth, helpers, cache
│   ├── main_automation.py         # AI engines (research, email, tracking)
│   ├── routes/
│   │   ├── auth.py                # Login/logout
│   │   ├── dashboard.py           # Dashboard with charts
│   │   ├── customers.py           # CRUD, CSV import/export
│   │   ├── research.py            # AI company research
│   │   ├── compose.py             # Email generation & scheduling
│   │   ├── tracking.py            # Email tracking & follow-ups
│   │   ├── batch_send.py          # Bulk email sending
│   │   ├── workflow.py            # Background automation
│   │   ├── attachments.py         # PDF management
│   │   ├── settings.py            # App configuration
│   │   └── auto_reply.py          # Auto-reply daemon status
│   └── services/
│       └── email_service.py       # Gmail API with retry logic
├── templates/                     # 15 Jinja2 templates
├── static/
│   ├── css/style.css
│   └── js/app.js
├── config/
│   ├── .env                       # Credentials (gitignored)
│   └── .env.template              # Config template
├── tests/                         # pytest test suite
├── attachments/                   # PDF attachments
├── logs/                          # Application logs
├── wsgi.py                        # Gunicorn entry point
├── Dockerfile                     # Docker deployment
├── docker-compose.yml
└── requirements.txt
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Dashboard** | KPI cards, pipeline chart, engagement pie chart, 14-day email activity |
| **Customers** | CRUD, CSV import/export, email validation, auto-research |
| **AI Research** | Company research via Claude API with pain point identification |
| **Email Compose** | AI-generated personalized emails with scheduling support |
| **Batch Send** | Send to multiple customers per pipeline stage with attachments |
| **Tracking** | Email history, reply detection, auto follow-up, scheduled sending |
| **Attachments** | Upload/manage PDFs, assign to pipeline stages |
| **Settings** | Configure sender info, rate limits, follow-up timing |
| **Auth** | Session-based login (configurable in .env) |

---

## Configuration

Edit `config/.env`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_SHEETS_ID=1abc...
SENDER_EMAIL=you@company.com

# Optional
APP_USERNAME=admin
APP_PASSWORD=quartz2024
MAX_EMAILS_PER_DAY=50
FOLLOWUP_DAYS=3
FLASK_ENV=development
```

---

## Deployment

### Development
```bash
python scripts/web_app.py
```

### Production (Gunicorn)
```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 wsgi:app
```

### Docker
```bash
docker-compose up -d
```

---

## Testing

```bash
pip install pytest
pytest tests/ -v
```

---

## Security

- Path traversal protection on all file operations
- XSS prevention via Jinja2 auto-escaping
- Email validation before sending (regex + format check)
- Input sanitization on settings (newline stripping, type validation)
- Thread-safe workflow execution
- File size limits (16MB global, 2MB CSV, 10MB PDF)
- Session-based authentication

---

## Prerequisites

- Python 3.9+
- Google Cloud project with Sheets API & Gmail API enabled
- Service account credentials (for Sheets)
- OAuth credentials (for Gmail)
- Anthropic API key (for AI features)

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup instructions.
