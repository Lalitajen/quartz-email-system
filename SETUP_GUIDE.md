# Quartz Email Outreach System - Setup Guide

## 🎯 System Overview

This system automates:
1. **AI Research**: Automatically research companies and contacts
2. **Email Tracking**: Monitor inbox for customer replies
3. **Auto-Reply**: Generate draft responses with AI
4. **Smart Attachments**: Select appropriate files based on pipeline stage

## 📋 Prerequisites

1. Google Account (for Sheets and Gmail)
2. Anthropic API Key (for Claude AI)
3. Python 3.9 or higher

## 🚀 Step-by-Step Setup

### Step 1: Google Sheets Setup

1. **Create a new Google Sheet**
   - Go to https://sheets.google.com
   - Create a new spreadsheet
   - Name it "Quartz Email System"

2. **Create three worksheets** (tabs at bottom):
   - `Customers` - For customer database
   - `Email_Tracking` - For email logs
   - `Pipeline_Stages` - For reference data

3. **Set up Customers sheet**:
   Copy these headers into Row 1:
   ```
   id | company_name | company_email | company_website | contact_name | contact_email | contact_department | pipeline_stage | tags | research_status | research_summary | pain_points | last_contact_date | response_status | notes
   ```

4. **Set up Email_Tracking sheet**:
   Copy these headers into Row 1:
   ```
   email_id | customer_id | company_name | contact_email | subject | sent_date | sent_time | pipeline_stage | email_type | attachments | status | opened | replied | reply_date | reply_content_summary | next_action | ai_confidence | reviewed_by
   ```

5. **Set up Pipeline_Stages sheet**:
   Copy these headers into Row 1:
   ```
   stage_number | stage_name | key_signals | default_attachments | typical_duration_days | conversion_rate_target | automation_rules
   ```
   
   Then copy this data (rows 2-8):
   ```
   1 | Prospecting | Outbound no response yet | brochure.pdf;company_profile.pdf | 7 | 15% | Auto-follow-up after 3 days
   2 | Initial Contact | General interest shown | technical_sheet.pdf;product_catalog.pdf | 5 | 30% | Send specs within 24 hours
   3 | Qualification | Asking specs | questionnaire.pdf;spec_sheet.pdf | 10 | 50% | AI fills questionnaire
   4 | Sample & Testing | Sample request | sample_request_form.pdf;coa.pdf | 30 | 60% | Schedule sample shipment
   5 | Negotiation | Price negotiation | quotation_personalized.pdf | 14 | 70% | Auto-generate quotation
   6 | Contract | Contract signing | contract_template.pdf;terms.pdf | 21 | 80% | Legal review required
   7 | Fulfillment | Delivery | shipping_docs.pdf;invoice.pdf | 60 | 95% | Generate documents
   ```

6. **Get your Google Sheets ID**:
   - Look at the URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`
   - Copy the SPREADSHEET_ID part
   - Save it for configuration

### Step 2: Google Cloud Setup (for API access)

1. **Enable Google Sheets and Gmail APIs**:
   - Go to https://console.cloud.google.com
   - Create a new project (or select existing)
   - Go to "APIs & Services" > "Library"
   - Enable:
     - Google Sheets API
     - Gmail API

2. **Create Service Account** (for Sheets):
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Name it "quartz-email-system"
   - Click "Done"
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key" > JSON
   - Download the JSON file
   - Rename it to `google_credentials.json`
   - Place it in your project folder

3. **Create OAuth Client** (for Gmail):
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Desktop app"
   - Name it "quartz-gmail-client"
   - Download the JSON file
   - Rename it to `gmail_credentials.json`
   - Place it in your project folder

4. **Share Google Sheet with Service Account**:
   - Open your Google Sheet
   - Click "Share" button
   - Paste the service account email (from google_credentials.json)
   - Format: `quartz-email-system@your-project.iam.gserviceaccount.com`
   - Give it "Editor" access

### Step 3: Anthropic API Setup

1. Get your API key:
   - Go to https://console.anthropic.com
   - Create account or log in
   - Go to "API Keys"
   - Create new key
   - Copy the key (starts with `sk-ant-`)

### Step 4: Python Environment Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   - Copy `config/.env.template` to `config/.env`
   - Edit `config/.env` with your values:
   ```
   ANTHROPIC_API_KEY=sk-ant-your_key_here
   GOOGLE_SHEETS_ID=your_spreadsheet_id_here
   SENDER_EMAIL=your_email@company.com
   ```

### Step 5: First Run

1. **Add sample customers to Google Sheets**:
   In the Customers sheet, add:
   ```
   CUST001 | ABC Semiconductors | info@abcsemi.com | https://abcsemi.com | John Smith | john.smith@abcsemi.com | Purchasing | 1 | hot;semiconductor | pending | | | | no_contact |
   ```

2. **Run the system**:
   ```bash
   python scripts/main_automation.py
   ```

3. **First run will**:
   - Authenticate with Gmail (browser will open)
   - Research companies marked as "pending"
   - Check for new email replies
   - Generate draft responses for review

## 📊 Using the System

### Daily Workflow

1. **Morning**: Run the script to process overnight replies
2. **Review**: Check Email_Tracking sheet for drafts (`reviewed_by = pending_review`)
3. **Approve/Edit**: Review AI-generated emails, make edits if needed
4. **Send**: Mark as approved and system sends emails
5. **Track**: Monitor pipeline progression in dashboard

### Adding New Customers

1. Open Google Sheets > Customers tab
2. Add new row with:
   - Unique `id` (e.g., CUST004)
   - Company details
   - Set `research_status = pending`
   - Set `pipeline_stage = 1`
3. Run script - AI will research automatically

### Reviewing Draft Emails

1. Open Email_Tracking sheet
2. Filter for `reviewed_by = pending_review`
3. Read the draft email details
4. Decision options:
   - **Approve**: Change to `reviewed_by = approved` → system sends
   - **Edit**: Change email content, then approve
   - **Reject**: Change to `reviewed_by = rejected`

## 🔧 Customization

### Modify Email Templates

Edit the prompts in `main_automation.py`:
- `EmailPersonalizationEngine.generate_email()` - Outbound emails
- `AutoReplyEngine.analyze_and_generate_reply()` - Reply emails

### Adjust Pipeline Stages

Edit `Pipeline_Stages` sheet in Google Sheets to:
- Change attachments for each stage
- Modify automation rules
- Adjust conversion targets

### Rate Limiting

Edit `config/.env`:
```
MAX_EMAILS_PER_DAY=50
RESEARCH_DELAY_SECONDS=2
```

## 🔐 Security Best Practices

1. **Never commit credentials**:
   - Add `*.json`, `.env` to `.gitignore`
   
2. **Rotate API keys** monthly

3. **Review auto-generated emails** before enabling auto-send

4. **Backup Google Sheets** weekly

## 📈 Dashboard & Analytics

Create a Dashboard sheet in Google Sheets with formulas:

**Total Customers**: `=COUNTA(Customers!A:A)-1`
**Emails Sent Today**: `=COUNTIF(Email_Tracking!F:F,TODAY())`
**Response Rate**: `=COUNTIF(Email_Tracking!L:L,"yes")/COUNTA(Email_Tracking!A:A)`
**By Stage**: `=COUNTIF(Customers!H:H,1)` (for stage 1, repeat for 2-7)

## 🐛 Troubleshooting

### Error: "Credentials not found"
- Ensure `google_credentials.json` and `gmail_credentials.json` are in project folder
- Check file permissions

### Error: "API quota exceeded"
- Google Sheets: 100 requests/100 seconds limit
- Gmail: 250 quota units/user/second
- Add delays between operations

### AI Research not working
- Check Anthropic API key is valid
- Verify website URLs are accessible
- Check rate limits

### Emails not sending
- Verify Gmail OAuth completed successfully
- Check `token.json` exists after first auth
- Ensure "Less secure app access" is NOT enabled (use OAuth2)

## 📞 Support

For issues:
1. Check logs in terminal output
2. Review Google Sheets for error messages
3. Verify all credentials are correct
4. Check API quotas and limits

## 🎯 Next Steps

After basic setup works:
1. Import your full customer list
2. Organize attachment library
3. Customize email templates
4. Set up scheduling (cron job for automated runs)
5. Build dashboard with Data Studio

## 🚀 Advanced Features (Future)

- LinkedIn integration for contact enrichment
- A/B testing different email templates
- Predictive lead scoring
- Multi-language support
- Mobile app for reviews
- CRM integration (HubSpot, Salesforce)
