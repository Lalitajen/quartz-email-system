# API & Credentials Setup Guide
## Quartz Email System v3.0

This guide explains how the automated API & Credentials system works and how to set it up easily.

---

## 🔐 Overview: How Credentials Work

The Quartz Email System uses **per-user encrypted credentials** stored in a secure SQLite database. Each user brings their own API keys and credentials, which are:

1. **Encrypted** using Fernet cipher (AES-256)
2. **Isolated** per user (no sharing between users)
3. **Stored** in SQLite database (not in files)
4. **Tested** automatically with one-click validation

---

## 📊 Credentials Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER SETUP (One-Time)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌──────────────────────────┐
         │   1. ANTHROPIC API KEY   │
         │   (AI Email Generation)  │
         └────────────┬─────────────┘
                      │
                      │ User pastes: sk-ant-api03-...
                      ▼
         ┌─────────────────────────────────┐
         │  ENCRYPTION (Fernet AES-256)    │
         │  Plain → Encrypted → SQLite     │
         └────────────┬────────────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │  2. GOOGLE SERVICE       │
         │     ACCOUNT JSON         │
         │  (Sheets Read/Write)     │
         └────────────┬─────────────┘
                      │
                      │ User pastes: {"type": "service_account", ...}
                      ▼
         ┌─────────────────────────────────┐
         │  VALIDATION (JSON Format)       │
         │  ENCRYPTION → SQLite            │
         └────────────┬────────────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │  3. GOOGLE SHEETS ID     │
         │  (Database)              │
         └────────────┬─────────────┘
                      │
                      │ Option A: Auto-create (click button)
                      │ Option B: Paste existing ID
                      ▼
         ┌─────────────────────────────────┐
         │  AUTO-CREATE SHEET (Optional)   │
         │  - Creates 3 worksheets         │
         │  - Adds all columns             │
         │  - Shares with service account  │
         │  - Returns Sheets ID            │
         └────────────┬────────────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │  4. GMAIL OAUTH TOKEN    │
         │  (Send Emails)           │
         └────────────┬─────────────┘
                      │
                      │ User clicks "Authorize Gmail"
                      ▼
         ┌─────────────────────────────────┐
         │  OAUTH FLOW                     │
         │  1. Redirect to Google          │
         │  2. User grants permissions     │
         │  3. Exchange code for tokens    │
         │  4. ENCRYPTION → SQLite         │
         └────────────┬────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    CREDENTIALS READY                        │
│  User can now: Send emails, Research, Track, Auto-reply   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step Setup

### Step 1: Anthropic API Key (AI Features)

**What it's for:**
- AI email generation
- Intent detection (95%+ accuracy)
- Customer research
- Auto-reply suggestions

**How to get it:**
1. Go to [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Sign up / Log in
3. Click "Create Key"
4. Copy the key (starts with `sk-ant-`)

**How to set it up:**
1. Go to **Settings → API & Credentials**
2. Paste your key in "Anthropic API Key" field
3. Click "Update API Key"
4. Click "Test Connection" to verify ✅

**Security:**
- Your key is encrypted with AES-256 before storage
- Never logged in plain text
- Only you can access it

---

### Step 2: Google Service Account (Sheets Access)

**What it's for:**
- Read customer data from Google Sheets
- Write email tracking data
- Update pipeline stages
- Auto-sync between app and sheets

**How to get it:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Create a new project (or use existing)
3. Enable **Google Sheets API** for your project
4. Go to **IAM & Admin → Service Accounts**
5. Click "Create Service Account"
6. Give it a name (e.g., `quartz-email-bot`)
7. Click "Create and Continue"
8. Skip roles (click "Continue" twice)
9. Click on the created service account
10. Go to "Keys" tab
11. Click "Add Key" → "Create New Key" → JSON
12. Download the JSON file

**How to set it up:**
1. Open the downloaded JSON file in a text editor
2. Copy **entire contents** (all the JSON)
3. Go to **Settings → API & Credentials**
4. Paste in "Service Account JSON" field
5. Click "Update Service Account"

**Important:** Note the service account email from the JSON:
```json
{
  "client_email": "quartz-email-bot@your-project.iam.gserviceaccount.com"
}
```
You'll need this email to share your Google Sheet!

---

### Step 3: Google Sheets ID (Your Database)

**What it's for:**
- Store customer contact information
- Track email send history
- Store email templates
- Your personal CRM database

**Option A: Auto-Create (EASIEST)**
1. Go to **Settings → API & Credentials**
2. Make sure Service Account is configured first
3. Click **"Auto-Create Sheet"**
4. ✅ Done! System creates the sheet and sets the ID automatically

**What Auto-Create does:**
- Creates a new Google Sheet in your account
- Adds 3 worksheets: `Customers`, `Email_Tracking`, `Email_Templates`
- Adds all required columns automatically
- Shares the sheet with your service account (Editor permission)
- Configures the Sheets ID in your account

**Option B: Use Existing Sheet**
1. Open your Google Sheet
2. Copy the ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/[THIS_IS_THE_ID]/edit
   ```
3. **IMPORTANT:** Share the sheet with your service account email:
   - Click "Share" button in Google Sheets
   - Paste the service account email
   - Set role to "Editor"
   - Uncheck "Notify people"
   - Click "Share"
4. Go to **Settings → API & Credentials**
5. Paste the Sheets ID
6. Click "Update Sheets ID"
7. Click "Test Connection" to verify ✅

**Required Columns (if creating manually):**

**Customers Sheet:**
- id, company_name, company_website, contact_name, contact_email
- contact_phone, industry, location, pipeline_stage, tags
- research_status, research_summary, pain_points, last_contact_date
- response_status, notes, engagement_level, urgency_score, buying_intent

**Email_Tracking Sheet:**
- tracking_id, customer_id, company_name, contact_email, subject
- stage, sent_date, opened, clicked, replied, reply_date
- reply_content_summary, status, next_action

**Email_Templates Sheet:**
- template_id, template_name, stage, subject, body, created_date, last_used

---

### Step 4: Gmail OAuth (Send Emails)

**What it's for:**
- Send personalized emails via Gmail API
- Read inbox for auto-reply detection
- Track email opens/clicks
- Professional sending (from your real Gmail)

**How to set it up:**
1. Go to **Settings → API & Credentials**
2. Click **"Authorize Gmail"**
3. You'll be redirected to Google
4. Select your Gmail account
5. Review permissions:
   - Send email on your behalf
   - Read your email messages
6. Click "Allow"
7. You'll be redirected back to Settings
8. ✅ Done! Token is encrypted and stored

**What happens behind the scenes:**
1. OAuth flow generates a code
2. App exchanges code for access token + refresh token
3. Tokens are encrypted with AES-256
4. Stored in your user database
5. Refresh token allows perpetual access (no re-auth needed)

**If it fails:**
- Check that Gmail API is enabled in your Google Cloud project
- Verify redirect URI matches: `http://localhost:5000/oauth/callback`
- Try clicking "Re-authorize Gmail" in Settings

---

## 🧪 Testing Your Credentials

After setting up each credential, use the **Test Connection** buttons:

### Test Anthropic API
```
What it does:
1. Makes a tiny API call to Claude
2. Asks AI to say "OK"
3. Verifies response

Success: ✅ API key is valid! Connection successful.
Failure: ❌ API key test failed: [error details]
```

### Test Google Sheets
```
What it does:
1. Connects using service account
2. Tries to read Customers sheet
3. Counts column headers

Success: ✅ Google Sheets connection successful! Found X columns.
Failure: ❌ Google Sheets test failed: [error details]
```

**Common errors:**
- "Permission denied" → Sheet not shared with service account
- "Sheet not found" → Wrong Sheets ID
- "Invalid credentials" → Service account JSON malformed

### Test Gmail
```
What it does:
1. Uses OAuth token to connect
2. Gets user profile
3. Shows connected email

Success: ✅ Gmail connection successful! Connected as: you@gmail.com
Failure: ❌ Gmail test failed: [error]. You may need to re-authorize.
```

---

## 🔒 Security Features

### Encryption at Rest
All credentials are encrypted using **Fernet (AES-256 CBC)** before storage:

```python
Plain:     sk-ant-api03-...
Encrypted: gAAAAABl... (256 bytes)
Storage:   SQLite BLOB column
```

**Encryption key sources:**
1. `CREDENTIAL_ENCRYPTION_KEY` environment variable (if set)
2. Flask secret key (auto-generated on first run)
3. Stored in `config/.flask_secret` (600 permissions)

### Credential Isolation
Each user has separate encrypted credentials:
```
User A: anthropic_api_key_enc = [encrypted data A]
User B: anthropic_api_key_enc = [encrypted data B]

User A cannot access User B's credentials
```

### No Plain Text Storage
- Credentials **never** written to log files
- Masked in UI (••••••••)
- Only decrypted in memory when needed
- Immediately cleared after use

---

## 🛠️ Troubleshooting

### Problem: "API key test failed"
**Solutions:**
1. Verify API key starts with `sk-ant-`
2. Check Anthropic Console that key is active
3. Try creating a new key
4. Copy-paste carefully (no extra spaces)

### Problem: "Google Sheets test failed: Permission denied"
**Solutions:**
1. Share sheet with service account email
2. Grant "Editor" permission (not "Viewer")
3. Make sure you clicked "Share" (not just typed email)
4. Wait 30 seconds for permissions to propagate

### Problem: "Google Sheets test failed: Sheet not found"
**Solutions:**
1. Double-check Sheets ID from URL
2. Copy only the ID portion (between /d/ and /edit)
3. Don't include the full URL
4. Try "Auto-Create Sheet" instead

### Problem: "Gmail test failed"
**Solutions:**
1. Click "Re-authorize Gmail" in Settings
2. Make sure you granted both "send" and "read" permissions
3. Check that Gmail API is enabled in Google Cloud Console
4. Verify redirect URI is configured correctly

### Problem: "Auto-Create Sheet failed"
**Solutions:**
1. Make sure Service Account is configured first
2. Check that Google Sheets API is enabled
3. Verify service account has correct permissions
4. Try creating the sheet manually instead

---

## 📋 Credential Update Workflow

### Updating Existing Credentials

**To update Anthropic API Key:**
1. Go to Settings → API & Credentials
2. Enter new key in field
3. Click "Update API Key"
4. Test with "Test Connection"

**To fix Google Sheets connection:**
1. Option A: Click "Auto-Create Sheet" (creates new)
2. Option B: Update Sheets ID manually
3. Test with "Test Connection"
4. If still failing, update Service Account

**To re-authorize Gmail:**
1. Click "Re-authorize Gmail"
2. Complete OAuth flow again
3. New token replaces old token
4. Test with "Test Connection"

---

## 🎯 Quick Setup Checklist

Use this checklist to ensure everything is configured:

- [ ] **Anthropic API Key**
  - [ ] Key pasted and saved
  - [ ] Test connection successful ✅
  - [ ] API calls working in app

- [ ] **Google Service Account**
  - [ ] JSON downloaded from GCP
  - [ ] JSON pasted and saved
  - [ ] Service account email noted

- [ ] **Google Sheets**
  - [ ] Sheet created (auto or manual)
  - [ ] Sheets ID configured
  - [ ] Sheet shared with service account (Editor)
  - [ ] Test connection successful ✅
  - [ ] Can open sheet from Settings

- [ ] **Gmail OAuth**
  - [ ] Authorized Gmail account
  - [ ] Permissions granted (send + read)
  - [ ] Test connection successful ✅
  - [ ] Shows correct email address

**All green?** You're ready to use the system! 🎉

---

## 🔄 Automated Credential Flow in Action

### When you send an email:
```
1. User clicks "Send Email"
   ↓
2. App retrieves encrypted Gmail token from database
   ↓
3. Token decrypted in memory (AES-256)
   ↓
4. Gmail API called with decrypted token
   ↓
5. Email sent
   ↓
6. Token cleared from memory
   ↓
7. Tracking data written to Google Sheets (using service account)
   ↓
8. Success message shown to user
```

### When AI generates email:
```
1. User requests AI email generation
   ↓
2. App retrieves encrypted Anthropic API key
   ↓
3. Key decrypted in memory
   ↓
4. Anthropic API called with customer context
   ↓
5. AI generates personalized email
   ↓
6. API key cleared from memory
   ↓
7. Generated email shown to user
```

### When checking email replies:
```
1. Automated check every X hours
   ↓
2. App retrieves encrypted Gmail token
   ↓
3. Token decrypted, inbox read
   ↓
4. New replies detected
   ↓
5. AI analyzes reply intent (using Anthropic API)
   ↓
6. Updates customer record in Google Sheets
   ↓
7. User notified of new replies
```

---

## 💡 Pro Tips

1. **Keep credentials safe:**
   - Never share API keys in screenshots
   - Don't commit credentials to git
   - Rotate keys periodically

2. **Use test connections:**
   - Test after initial setup
   - Test after any changes
   - Test if something stops working

3. **Monitor API usage:**
   - Anthropic Console shows API usage
   - Google Cloud Console shows API quotas
   - Set up billing alerts

4. **Backup your Sheets ID:**
   - Note down your Sheets ID somewhere safe
   - Export sheet data periodically
   - Keep service account JSON backed up

5. **Auto-create vs Manual:**
   - Auto-create: Fastest, automatic setup
   - Manual: More control, use existing sheet

---

## 📞 Support

**Still having issues?**
- Check the troubleshooting section above
- Review error messages carefully
- Test connections one by one
- Try the auto-create options
- Re-authorize if OAuth fails

**System works when:**
- ✅ All 4 credentials configured
- ✅ All test connections pass
- ✅ Status overview shows 4 green checkmarks

---

**Last Updated:** February 14, 2026
**Version:** 3.0.0
**Guide:** API & Credentials Setup
