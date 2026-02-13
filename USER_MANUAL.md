# Quartz Email Outreach System - User Manual

**Version 3.0 - Security Hardened Edition**

---

## Table of Contents
1. [Introduction](#introduction)
2. [Security Features](#security-features)
3. [Initial Setup](#initial-setup)
4. [User Guide](#user-guide)
5. [Security Best Practices](#security-best-practices)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)

---

## Introduction

The Quartz Email Outreach System is a secure, AI-powered B2B email automation platform designed for high-purity quartz mining outreach. This system has been hardened against OWASP Top 10 security vulnerabilities.

### Key Features
- ✅ **OWASP Top 10 Compliant** - Industry-standard security
- 🔐 **CSRF Protection** - All forms protected against cross-site attacks
- 🛡️ **Rate Limiting** - Brute-force attack prevention
- 🔒 **Secure Sessions** - 2-hour auto-logout, HttpOnly cookies
- 🚫 **XSS Prevention** - All user input properly escaped
- 🌐 **SSRF Protection** - URL validation for external requests
- 📝 **Security Logging** - All authentication events logged
- 🔑 **Password Hashing** - Industry-standard pbkdf2/scrypt support

---

## Security Features

### A01: Broken Access Control - ✅ FIXED
- **CSRF tokens** on all POST forms
- **Rate limiting**: 200 requests/minute globally
- **Brute force protection**: 5 failed login attempts = 5-minute lockout
- **Session management**: 2-hour timeout, HttpOnly, SameSite cookies

### A02: Cryptographic Failures - ✅ FIXED
- **Password hashing** support (pbkdf2, scrypt)
- **Secret key**: 32-byte random key, file permissions 0600
- **API keys masked** in settings UI
- **OAuth tokens** stored as JSON (not pickle)

### A03: Injection - ✅ FIXED
- **XSS protection**: All user input escaped with `|e` filter
- **Input length limits**: maxlength on all text fields
- **Flash message sanitization**: No internal errors exposed

### A04: Insecure Design - ✅ FIXED
- **Global rate limiting**: 200 req/min
- **Input validation**: Email format, numeric ranges
- **Length restrictions**: Prevents buffer overflow attacks

### A05: Security Misconfiguration - ✅ FIXED
- **Security headers**: CSP, X-Frame-Options, X-XSS-Protection, etc.
- **Debug mode**: Binds to localhost only (not 0.0.0.0)
- **Error handlers**: Generic 404/500 pages (no stack traces)
- **HSTS** in production mode

### A07: Authentication Failures - ✅ FIXED
- **Brute force protection**: IP-based lockout
- **Session security**: HttpOnly, Secure, SameSite
- **Session timeout**: 2 hours
- **Login logging**: All attempts logged with IP

### A08: Data Integrity - ✅ FIXED
- **JSON token storage**: Replaces insecure pickle
- **File permissions**: 0600 on sensitive files
- **Credential encryption**: At rest

### A09: Security Logging - ✅ FIXED
- **Login events**: Success, failure, lockout
- **Generic error messages**: No internal details leaked
- **Audit trail**: All security events logged

### A10: SSRF - ✅ FIXED
- **URL validation**: Blocks private IPs, localhost, cloud metadata
- **Scheme validation**: Only http/https allowed
- **Response limits**: 1MB max

---

## Initial Setup

### Prerequisites
- Python 3.8+
- Google Cloud account (for Sheets & Gmail)
- Anthropic API key
- GitHub account (for deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lalita/quartz-email-system.git
   cd quartz-email-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create `config/.env`:
   ```env
   # Authentication (IMPORTANT: Change these!)
   APP_USERNAME=your_admin_username
   APP_PASSWORD=pbkdf2:sha256:... # Use hashed password (see below)
   FLASK_SECRET_KEY=your-random-32-byte-key

   # Google Services
   GOOGLE_SHEETS_ID=your_google_sheets_id
   GMAIL_CREDENTIALS_PATH=gmail_credentials.json

   # AI
   ANTHROPIC_API_KEY=sk-ant-...

   # Email Config
   SENDER_NAME=Your Name
   SENDER_EMAIL=you@company.com
   SENDER_TITLE=Business Development Manager
   COMPANY_NAME=Your Company
   COMPANY_PHONE=+1-xxx-xxx-xxxx
   COMPANY_WEBSITE=www.yourcompany.com
   COMPANY_ADDRESS=Your Address

   # Security Settings
   MAX_EMAILS_PER_DAY=50
   RESEARCH_DELAY_SECONDS=2
   FOLLOWUP_DAYS=3

   # Environment
   FLASK_ENV=development  # Change to 'production' when deploying
   ```

5. **Generate a hashed password**
   ```bash
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_secure_password'))"
   ```

   Copy the output to `APP_PASSWORD` in `.env`

6. **Set up Google Services**

   a. **Google Sheets**:
   - Create a new Google Sheet
   - Copy the Sheet ID from the URL
   - Add to `.env` as `GOOGLE_SHEETS_ID`

   b. **Gmail OAuth**:
   ```bash
   python authenticate_gmail.py
   ```
   Follow the browser prompt to authorize

   c. **Service Account** (for Sheets API):
   - Create service account in Google Cloud Console
   - Download JSON key
   - Save as `service_account.json` in project root

7. **Run the application**
   ```bash
   python scripts/web_app.py
   ```

   Access at: `http://127.0.0.1:5000`

---

## User Guide

### Login

1. Navigate to `http://127.0.0.1:5000/login`
2. Enter username and password
3. **Security Note**: After 5 failed attempts, your IP will be locked out for 5 minutes

### Dashboard

The dashboard shows:
- Total customers
- Email statistics
- Engagement breakdown
- Recent activity

### Managing Customers

#### Adding a Customer
1. Go to **Customers** → **Add Customer**
2. Fill in required fields:
   - Company Name
   - Contact Name
   - Contact Email (validated)
   - Company Website
   - Pipeline Stage (1-7)
3. Click **Add Customer**
4. Optional: Enable **Auto-Research** to gather AI insights immediately

#### Editing a Customer
1. Click on customer name to view details
2. Click **Edit Customer**
3. Modify fields
4. Click **Save Changes**

#### Importing from CSV
1. Go to **Customers** → **Import CSV**
2. Upload CSV with columns:
   - `company_name`
   - `contact_name`
   - `contact_email`
   - `company_website`
   - `pipeline_stage`
3. Click **Import**

### AI Research

1. Go to **Research** tab
2. Click **Run Research** on individual customers
3. Or click **Run All** to research all customers without data
4. AI will:
   - Scrape company website (with SSRF protection)
   - Analyze business relevance
   - Generate engagement strategy
   - Suggest email approach

### Composing Emails

#### Manual Compose
1. Go to **Compose** tab
2. Select customer
3. Choose pipeline stage
4. Click **Generate Email**
5. Review AI-generated subject and body
6. Edit as needed
7. Select attachments (from `/attachments` folder)
8. Click **Send Now** or **Schedule**

#### Batch Send
1. Go to **Batch Send** tab
2. Filter by:
   - Pipeline stage
   - Engagement level
   - Date range
3. Select customers
4. Preview email template
5. Click **Send Batch**
6. **Rate Limit**: Max 50 emails/day (configurable)

### Email Tracking

1. Go to **Tracking** tab
2. View all sent emails
3. Status indicators:
   - ✅ **Sent**: Email delivered
   - 📬 **Queued**: Scheduled to send
   - 📧 **Opened**: Customer opened email
   - 💬 **Replied**: Customer responded

#### Check Replies
1. Click **Check Replies**
2. System fetches new Gmail messages
3. AI classifies reply type:
   - Quotation Request
   - Sample Request
   - Technical Info Request
   - Declined
   - General Reply
4. Updates pipeline stage automatically

### Auto-Reply

1. Go to **Auto-Reply** tab
2. Click **Start Daemon**
3. System monitors Gmail inbox every X hours
4. Auto-generates replies for:
   - Quotation requests
   - Technical questions
   - Sample inquiries
5. **Safety**: Requires 0.8 confidence threshold
6. All replies logged for review

### Attachments

1. Go to **Attachments** tab
2. Upload PDFs (max 10MB each)
3. Files stored in `/attachments` directory
4. **Security**: Path traversal protection enabled
5. Use in email composition

### Settings

1. Go to **Settings** tab
2. Configure:
   - **Email Settings**: Sender info, company details
   - **API Keys**: View masked keys (edit in `.env`)
   - **Limits**: Max emails/day, research delay
   - **Follow-up**: Auto follow-up after X days
3. Click **Save Settings**

**Security Note**: Settings are sanitized against XSS attacks

---

## Security Best Practices

### For Administrators

1. **Use Strong Passwords**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - Use a password manager
   - Hash passwords before storing in `.env`

2. **Protect Credentials**
   ```bash
   # Never commit these files to git:
   config/.env
   config/.flask_secret
   token.json
   token.pickle
   gmail_credentials.json
   service_account.json
   ```

3. **Production Deployment**
   ```env
   # In config/.env
   FLASK_ENV=production
   FLASK_SECRET_KEY=<strong-random-key>
   ```

   This enables:
   - HTTPS-only cookies
   - HSTS headers
   - Stricter CSP

4. **Monitor Logs**
   ```bash
   tail -f logs/web_app.log
   ```

   Watch for:
   - Failed login attempts
   - Rate limit violations
   - SSRF blocking events

5. **Regular Updates**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

6. **File Permissions**
   ```bash
   chmod 600 config/.env
   chmod 600 config/.flask_secret
   chmod 600 token.json
   chmod 600 service_account.json
   ```

### For Users

1. **Session Security**
   - Log out when done (don't just close browser)
   - Sessions expire after 2 hours
   - Use private/incognito for shared computers

2. **Email Safety**
   - Review AI-generated emails before sending
   - Don't include sensitive data in outreach
   - Verify recipient addresses

3. **API Key Protection**
   - Don't share your Anthropic API key
   - Rotate keys if compromised
   - Monitor API usage in Anthropic dashboard

4. **Data Privacy**
   - Customer data stored in Google Sheets
   - Email logs tracked in sheets
   - No data sold or shared with third parties

---

## Troubleshooting

### Login Issues

**Problem**: "Too many failed attempts"
- **Cause**: 5 failed logins in 5 minutes
- **Solution**: Wait 5 minutes, or restart the app to clear lockout

**Problem**: "Invalid credentials"
- **Cause**: Wrong username/password
- **Solution**: Check `config/.env` for `APP_USERNAME` and `APP_PASSWORD`

### Email Sending Issues

**Problem**: "Gmail not authenticated"
- **Solution**: Run `python authenticate_gmail.py`

**Problem**: "Rate limit exceeded"
- **Cause**: Sent more than MAX_EMAILS_PER_DAY
- **Solution**: Increase limit in Settings or wait 24 hours

**Problem**: "Invalid email address"
- **Cause**: Email format validation failed
- **Solution**: Fix email format (must have @domain.ext)

### Research Issues

**Problem**: "URL blocked by security policy"
- **Cause**: SSRF protection blocked private IP or localhost
- **Solution**: Ensure company_website is a public URL (not internal)

**Problem**: "Anthropic API key not configured"
- **Solution**: Add `ANTHROPIC_API_KEY` to `config/.env`

### CSRF Token Issues

**Problem**: "The CSRF token is missing"
- **Cause**: Form submitted without csrf_token field
- **Solution**: Ensure you're using the latest templates with CSRF tokens

**Problem**: "The CSRF token is invalid"
- **Cause**: Session expired or token mismatch
- **Solution**: Refresh the page and try again

---

## API Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_USERNAME` | No | `admin` | Login username |
| `APP_PASSWORD` | No | `quartz2024` | Login password (use hashed) |
| `FLASK_SECRET_KEY` | No | Auto-generated | Session encryption key |
| `FLASK_ENV` | No | `development` | `development` or `production` |
| `GOOGLE_SHEETS_ID` | Yes | - | Google Sheets ID |
| `ANTHROPIC_API_KEY` | Yes | - | Claude API key |
| `SENDER_NAME` | Yes | - | Your name for emails |
| `SENDER_EMAIL` | Yes | - | Your email address |
| `MAX_EMAILS_PER_DAY` | No | `50` | Daily email limit |
| `RESEARCH_DELAY_SECONDS` | No | `2` | Delay between research requests |
| `FOLLOWUP_DAYS` | No | `3` | Auto follow-up after X days |

### Security Headers

The app sets the following security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Browser XSS filter |
| `Content-Security-Policy` | (see code) | Restricts resource loading |
| `Strict-Transport-Security` | `max-age=31536000` | Forces HTTPS (prod only) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limits referrer info |
| `Permissions-Policy` | Denies geolocation, camera, mic | Restricts browser APIs |

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Global | 200 requests | 1 minute |
| `/login` | 5 attempts | 5 minutes (then lockout) |

### File Size Limits

| File Type | Max Size |
|-----------|----------|
| All uploads | 16 MB |
| CSV imports | 2 MB (implied) |
| PDF attachments | 10 MB |

---

## Deployment Guide

### Deploying to Production

1. **Set environment to production**
   ```env
   FLASK_ENV=production
   ```

2. **Use a production WSGI server**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 scripts.web_app:create_app()
   ```

3. **Set up reverse proxy (nginx)**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **Enable firewall**
   ```bash
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

5. **Set up SSL/TLS**
   - Use Let's Encrypt: `certbot --nginx -d your-domain.com`
   - Or upload custom certificates

6. **Monitor logs**
   ```bash
   tail -f logs/web_app.log
   tail -f /var/log/nginx/error.log
   ```

---

## Support

- **Documentation**: See other guides in project root
- **Issues**: https://github.com/lalita/quartz-email-system/issues
- **Security**: Report vulnerabilities privately to security@yourcompany.com

---

## License

Proprietary - All rights reserved

---

## Changelog

### v3.0 - Security Hardened Edition (2026-02-13)
- ✅ OWASP Top 10 compliance
- ✅ CSRF protection on all forms
- ✅ Rate limiting and brute force protection
- ✅ XSS prevention with input escaping
- ✅ SSRF protection for URL scraping
- ✅ Secure session management
- ✅ Password hashing support
- ✅ Security logging and monitoring
- ✅ JSON token storage (replaces pickle)
- ✅ Security headers (CSP, HSTS, etc.)

### v2.0 - Modular Refactor
- Modular blueprint architecture
- Jinja2 templates
- Improved error handling

### v1.0 - Initial Release
- Basic email automation
- AI-powered research
- Google Sheets integration

---

**End of User Manual**
