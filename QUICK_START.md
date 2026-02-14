# Quick Start Guide - Smart Setup Assistant

## 🚀 Start Using Smart Setup in 3 Steps

### Step 1: Start the Web App
```bash
cd /Users/lalita/Downloads/quartz-email-system
python scripts/web_app.py
```

**You'll see:**
```
=======================================================
  Quartz Email Outreach System - Web Interface v3.0
  Refactored: Modular Routes + Jinja2 Templates
=======================================================
  Templates: /Users/lalita/Downloads/quartz-email-system/templates
  Static:    /Users/lalita/Downloads/quartz-email-system/static
  Logs:      /Users/lalita/Downloads/quartz-email-system/logs
=======================================================
  Login credentials configured via config/.env
  (APP_USERNAME, APP_PASSWORD)
=======================================================
 * Running on http://127.0.0.1:5000
```

---

### Step 2: Access Smart Setup
Open your browser and navigate to:
```
http://localhost:5000/smart-setup
```

Or login first at `http://localhost:5000/login` then click **"Smart Setup"** in the navigation menu.

---

### Step 3: Complete One-Click Setup

#### Option A: Quick Configuration (RECOMMENDED - 2 minutes)

1. **Get Anthropic API Key:**
   - Visit: https://console.anthropic.com/settings/keys
   - Click "Create Key"
   - Copy the key (starts with `sk-ant-`)

2. **Get Google Service Account JSON:**
   - Visit: https://console.cloud.google.com/iam-admin/serviceaccounts
   - Create service account
   - Download JSON key file
   - Open in text editor, copy entire contents

3. **Paste Both in Quick Config Form:**
   - Scroll to "Quick Configuration" section
   - Paste API key in first field
   - Paste entire JSON in second field
   - Click: **"Quick Setup - Auto-Configure Everything"**

4. **Authorize Gmail (1 click):**
   - You'll be redirected to Google
   - Select your Gmail account
   - Click "Allow"
   - Done! 🎉

**Total Time:** ~2 minutes

---

#### Option B: Auto-Complete (if you have some credentials)

If you already configured API key and Service Account:
1. Click: **"Auto-Complete Setup"** button
2. System auto-creates Google Sheet
3. Redirects to Gmail authorization
4. Done! 🎉

---

#### Option C: Test Existing Credentials

If all 4 credentials are configured:
1. Click: **"Test All Connections"**
2. See results for all 4 services
3. Green ✅ = working, Red ❌ = needs attention

---

## 📊 What You'll See

### Progress Dashboard

**0% Complete (Red Bar):**
```
🔴 0% - Let's Get Started
0 of 4 steps completed
```

**50% Complete (Yellow Bar):**
```
🟡 50% - Halfway Done
2 of 4 steps completed
```

**75% Complete (Blue Bar):**
```
🔵 75% - Almost There!
3 of 4 steps completed
```

**100% Complete (Green Bar):**
```
🟢 100% - All Set! 🎉
4 of 4 steps completed
```

---

### Credential Status Cards

**Card 1: Anthropic API Key**
- Icon: 🤖 Robot
- Status: ⚠️ Pending → ✅ Configured
- Actions: Test Connection, Update

**Card 2: Google Service Account**
- Icon: 📄 File Code
- Status: ⚠️ Pending → ✅ Configured
- Actions: Update

**Card 3: Google Sheets ID**
- Icon: 📊 Table
- Status: ⚠️ Pending → ✅ Configured
- Actions: Auto-Create Sheet, Test Connection

**Card 4: Gmail OAuth**
- Icon: ✉️ Envelope
- Status: ⚠️ Pending → ✅ Configured
- Actions: Authorize Gmail, Test Connection

---

## 🎯 What Happens Behind the Scenes

### Quick Config Workflow
```
1. You paste API key + Service Account JSON
   ↓
2. System validates format
   ↓
3. Both encrypted with AES-256 and saved to SQLite
   ↓
4. System auto-creates Google Sheet:
   - Creates 3 worksheets (Customers, Email_Tracking, Email_Templates)
   - Adds all 19 columns to Customers sheet
   - Adds all 14 columns to Email_Tracking sheet
   - Shares with your service account (Editor permission)
   - Saves Sheets ID to your account
   ↓
5. Redirects to Gmail OAuth (Google's login page)
   ↓
6. You click "Allow"
   ↓
7. Google sends code back to app
   ↓
8. App exchanges code for access token + refresh token
   ↓
9. Tokens encrypted and saved
   ↓
10. Redirects to dashboard
   ↓
11. 100% Complete! Ready to send emails 🎉
```

**Security:**
- ✅ All credentials encrypted with Fernet (AES-256)
- ✅ CSRF protection on all forms
- ✅ Input validation (API key format, JSON structure)
- ✅ Never logged in plain text
- ✅ Session timeouts (2 hours)

---

## 🧪 Verify Installation

Run the integration test:
```bash
python3 test_smart_setup_integration.py
```

**Expected output:**
```
============================================================
  Smart Setup Assistant - Integration Test Suite
============================================================
✅ PASS  Module Imports
✅ PASS  Blueprint Registration
✅ PASS  App Creation & Routes
✅ PASS  Template Existence
✅ PASS  Navigation Link
✅ PASS  Status Analysis Logic
============================================================
  6/6 tests passed (100%)
============================================================

🎉 All tests passed! Smart Setup is ready to use.
```

---

## 📁 Files Overview

### Backend (Python)
- **scripts/routes/smart_setup.py** (368 lines)
  - `/smart-setup` - Main dashboard
  - `/smart-setup/auto-complete` - Auto-configure remaining steps
  - `/smart-setup/quick-config` - One-form submission
  - `/smart-setup/test-all` - Bulk credential testing

### Frontend (HTML)
- **templates/smart_setup.html** (359 lines)
  - Progress bar with color coding
  - 4 credential status cards
  - Quick configuration form
  - Auto-complete button
  - Accordion setup guide

### Documentation
- **SMART_SETUP_GUIDE.md** (571 lines) - Complete integration guide
- **API_CREDENTIALS_GUIDE.md** (527 lines) - Detailed credential setup
- **QUICK_START.md** (this file) - Quick start guide

### Tests
- **test_smart_setup_integration.py** (290 lines) - Automated tests

---

## 🎬 Video Tutorial Workflow

### Scenario: Brand New User (Zero Configuration)

**Time: 0:00 - Start**
1. Open terminal
2. Run: `python scripts/web_app.py`
3. Open browser: `http://localhost:5000`

**Time: 0:30 - Login**
4. Login with credentials from `config/.env`
5. Click "Smart Setup" in navigation

**Time: 1:00 - See Dashboard**
6. See red progress bar: "0% - Let's Get Started"
7. See 4 cards all with ⚠️ Pending badges

**Time: 1:30 - Get API Key**
8. Open new tab: https://console.anthropic.com/settings/keys
9. Create new key
10. Copy key (starts with `sk-ant-`)

**Time: 2:00 - Get Service Account**
11. Open new tab: https://console.cloud.google.com/iam-admin/serviceaccounts
12. Create service account
13. Download JSON key file
14. Open in text editor, copy all

**Time: 3:00 - Paste Credentials**
15. Return to Smart Setup page
16. Paste API key in first field
17. Paste entire JSON in second field
18. Click "Quick Setup - Auto-Configure Everything"

**Time: 3:30 - Auto-Creation**
19. See flash messages:
    - "✅ Anthropic API key saved"
    - "✅ Service account saved"
    - "✅ Google Sheet created (ID: ...)"
20. Automatically redirected to Google OAuth

**Time: 4:00 - Gmail OAuth**
21. Select Gmail account
22. Review permissions (send + read)
23. Click "Allow"

**Time: 4:30 - Complete!**
24. Redirected to dashboard
25. See green checkmark: "Setup complete!"
26. Can now send emails

**Total Time: 4 minutes 30 seconds** (including getting credentials from Google/Anthropic)

---

## 🆘 Troubleshooting

### Issue: "API key test failed"
**Solution:** Check that key starts with `sk-ant-` and is active in Anthropic Console

### Issue: "Failed to create sheet: Permission denied"
**Solution:** Enable Google Sheets API in Google Cloud Console, wait 30 seconds

### Issue: "Gmail test failed: Token expired"
**Solution:** Click "Re-authorize Gmail" button

### Issue: Progress bar stuck at 75%
**Solution:** Click "Test All Connections" to see which credential is missing

---

## 📞 Need Help?

**Documentation:**
- [SMART_SETUP_GUIDE.md](SMART_SETUP_GUIDE.md) - Complete guide
- [API_CREDENTIALS_GUIDE.md](API_CREDENTIALS_GUIDE.md) - Credential details
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - System overview

**Test Integration:**
```bash
python3 test_smart_setup_integration.py
```

**Check Logs:**
```bash
tail -f logs/app.log
```

---

## ✅ Next Steps After Setup

Once you reach 100% completion:

1. **Add Customers:**
   - Navigate to `/customers`
   - Import CSV or add manually
   - Each customer gets added to your Google Sheet

2. **Research Customers:**
   - Go to `/research`
   - Select customer
   - AI analyzes their website and finds pain points

3. **Compose Personalized Emails:**
   - Go to `/compose`
   - Select customer and stage
   - AI generates personalized email based on research

4. **Send Batch Emails:**
   - Go to `/batch_send`
   - Select multiple customers
   - Send personalized emails to all at once

5. **Track Engagement:**
   - Go to `/tracking`
   - See email opens, clicks, replies
   - AI analyzes reply intent automatically

6. **Use Auto-Reply:**
   - Go to `/auto-reply`
   - AI detects intent from customer replies
   - Generates suggested responses

7. **View AI Insights:**
   - Go to `/ai-insights`
   - See hot leads, upsell opportunities
   - Get AI-powered recommendations

---

**Last Updated:** February 14, 2026
**Version:** 1.0.0
**Status:** ✅ Production Ready

🎉 **Enjoy your AI-powered email outreach system!**
