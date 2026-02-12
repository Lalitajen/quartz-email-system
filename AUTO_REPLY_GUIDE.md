# 24/7 Automated Email Response System

## 🎯 What It Does

This system **automatically monitors your Gmail** and responds to interested customers 24/7:

✅ **Checks every 5 seconds** for new emails
✅ **AI analyzes** customer interest level
✅ **Auto-replies** with personalized messages
✅ **Attaches PDFs** based on pipeline stage
✅ **Tracks everything** in Google Sheets
✅ **Runs continuously** until you stop it

---

## 🚀 Quick Start

### 1. Make Sure Gmail OAuth is Complete

```bash
python3 authenticate_gmail.py
```

Complete the browser authentication if you haven't already.

### 2. Start the Auto-Reply Daemon

```bash
./start_auto_reply.sh
```

You'll see:
```
✅ Auto-Reply Daemon started!
   PID: 12345
   Log: /tmp/auto_reply.log

System is now monitoring emails 24/7! 🎉
```

### 3. Monitor Status

```bash
./monitor_status.sh
```

Shows:
- Running status
- Recent activity
- Statistics (emails processed, sent, failed)

### 4. View Live Log

```bash
tail -f /tmp/auto_reply.log
```

Watch emails being processed in real-time!

### 5. Stop When Needed

```bash
./stop_auto_reply.sh
```

---

## 🔄 How It Works

### Email Detection (Every 5 seconds)

```
┌─────────────────────────────────────────┐
│  Daemon checks Gmail inbox              │
│  ↓                                       │
│  Finds unread emails                    │
│  ↓                                       │
│  AI analyzes each email                 │
└─────────────────────────────────────────┘
```

### AI Analysis

The AI determines:
1. **Interest Level**: HIGH / MEDIUM / LOW / NOT_INTERESTED
2. **Pipeline Stage**: 1-9 based on content
3. **What they're asking for**

### Auto-Response

Based on the stage, system:
1. **Generates personalized reply**
2. **Attaches relevant PDFs**
3. **Sends email automatically**
4. **Marks original as read**
5. **Logs to Google Sheets**

---

## 📎 Auto-Attached PDFs by Stage

| Stage | Name | PDFs Attached |
|-------|------|---------------|
| **1** | Prospecting | 01_Brochure.pdf |
| **2** | Initial Contact | 01_Brochure.pdf, 02_Technical_Data_Sheet.pdf |
| **3** | Qualification | 02_Technical_Data_Sheet.pdf, 04_Detailed_Brochure.pdf |
| **4** | Sample & Testing | 02_Technical_Data_Sheet.pdf, Sample_Request_Form.pdf |
| **5** | Negotiation | 03_Quotation.pdf |
| **6** | Contract | Contract_Template.pdf, 03_Quotation.pdf |
| **7** | Fulfillment | COA.pdf, Shipping_Docs.pdf |
| **8** | Follow-Up | Customer_Satisfaction_Survey.pdf |
| **9** | Repeat Customer | VIP_Discount_Program.pdf, Bulk_Order_Benefits.pdf |

---

## 🔍 Trigger Keywords

The AI looks for these keywords to determine stage:

### Stage 1 - Prospecting
- interested, tell me more, learn more, info, information

### Stage 2 - Initial Contact
- specifications, specs, technical, data sheet, details

### Stage 3 - Qualification
- ICP-MS, boron, purity, analysis, composition, impurities

### Stage 4 - Sample & Testing
- sample, trial, test, 2-5kg, lab, testing

### Stage 5 - Negotiation
- price, quote, quotation, cost, FOB, CIF, pricing

### Stage 6 - Contract
- contract, agreement, terms, payment, order

### Stage 7 - Fulfillment
- delivery, shipping, invoice, COA, shipment

### Stage 8 - Follow-Up
- feedback, satisfied, review, quality, reorder

### Stage 9 - Repeat Customer
- repeat, again, more, container, bulk, regular

---

## 📊 Tracking & Logs

### Google Sheets - "Auto Replies" Tab

Logs every auto-reply with:
- Timestamp
- Customer email
- Subject
- Interest level
- Pipeline stage
- Attachments sent
- Status (Sent/Failed)

### Log File: /tmp/auto_reply.log

Real-time activity log showing:
```
📧 Processing email from: customer@example.com
   Subject: Interested in high-purity quartz
   🤖 Analyzing with AI...
   Interest: HIGH | Stage: 2
   ✍️  Generating reply...
   📎 Attaching: 01_Brochure.pdf, 02_Technical_Data_Sheet.pdf
   📤 Sending auto-reply...
   ✅ Auto-reply sent!
```

---

## 🎛️ Configuration

### Change Check Interval

Edit `auto_reply_daemon.py` line 42:
```python
CHECK_INTERVAL = 5  # Seconds (change to 10, 30, etc.)
```

### Customize Auto-Reply Template

The AI generates replies based on:
- Customer's original email
- Pipeline stage
- Available attachments

To customize the prompt, edit the `generate_auto_reply()` function in `auto_reply_daemon.py`.

---

## 🔧 Troubleshooting

### Daemon Won't Start

**Problem:** `❌ Gmail not authenticated!`
**Solution:** Run `python3 authenticate_gmail.py`

**Problem:** `❌ Google Sheets credentials missing!`
**Solution:** Check `service_account.json` exists

**Problem:** `❌ config/.env not found!`
**Solution:** Create config/.env with API keys

### No Emails Being Processed

1. **Check daemon is running:**
   ```bash
   ./monitor_status.sh
   ```

2. **Check log for errors:**
   ```bash
   tail -20 /tmp/auto_reply.log
   ```

3. **Verify Gmail has unread emails:**
   - Log into Gmail
   - Check inbox for unread messages

### Auto-Replies Not Sending

**Problem:** AI analysis but no send
**Check:**
1. Gmail API quota (might be rate-limited)
2. Attachment files exist in `attachments/` folder
3. Log file for specific error messages

### High API Costs

**Problem:** Too many AI calls
**Solution:**
- Increase `CHECK_INTERVAL` to 30-60 seconds
- Add email filtering (only process specific senders)
- Cache AI analysis results

---

## 💡 Pro Tips

### 1. Run on Server

For true 24/7 operation, run on a server:
```bash
ssh your-server
cd quartz-email-system
./start_auto_reply.sh
```

Daemon keeps running even if you disconnect!

### 2. Multiple Instances

Run different daemons for different purposes:
- One for auto-replies
- One for tracking only
- One for specific customer segments

### 3. Email Filtering

Add filters to only process certain emails:
```python
# In get_unread_emails(), add:
q='is:unread in:inbox from:@targetdomain.com'
```

### 4. Custom Responses by Industry

Modify AI prompt to generate industry-specific replies:
```python
# Add to prompt:
"Customer Industry: Glass Manufacturing"
"Use technical terminology appropriate for this industry."
```

---

## 📈 Expected Performance

### Typical Metrics:

- **Check Speed:** <1 second per check
- **Email Processing:** 5-10 seconds per email
- **AI Analysis:** 2-3 seconds
- **Reply Generation:** 2-3 seconds
- **Email Sending:** 1-2 seconds

### Resource Usage:

- **Memory:** ~100-200 MB
- **CPU:** <5% (mostly idle)
- **API Calls:** 2 per email (analysis + reply)
- **Gmail API:** 1 read per 5 seconds, 1 send per reply

---

## 🛡️ Safety Features

### Built-in Protections:

1. **No duplicate replies** - Tracks processed email IDs
2. **Marks as read** - Won't process same email twice
3. **Error handling** - Continues if one email fails
4. **Logging** - Full audit trail
5. **Graceful shutdown** - Ctrl+C stops cleanly

### Not Interested Filter:

If AI detects customer is NOT interested:
- ❌ No auto-reply sent
- ✅ Email marked as read
- ✅ Logged for records

---

## 📞 Commands Reference

```bash
# Start daemon
./start_auto_reply.sh

# Check status
./monitor_status.sh

# View live log
tail -f /tmp/auto_reply.log

# Stop daemon
./stop_auto_reply.sh

# Restart daemon
./stop_auto_reply.sh && ./start_auto_reply.sh

# Test Gmail auth
python3 authenticate_gmail.py

# Test AI generation
python3 test_email_generation.py
```

---

## ✅ System Requirements

- ✅ Gmail OAuth completed (`token.pickle` exists)
- ✅ Google Sheets credentials (`service_account.json`)
- ✅ Anthropic API key with credits
- ✅ Python 3.7+
- ✅ All dependencies installed
- ✅ PDF attachments in `attachments/` folder

---

## 🎉 Success Criteria

Your system is working correctly when:

1. ✅ Daemon shows as "RUNNING" in monitor
2. ✅ Log shows "System running" every 5 minutes
3. ✅ Test emails get auto-replied within 5-10 seconds
4. ✅ Google Sheets logs show new entries
5. ✅ Customers receive personalized replies with correct PDFs

---

**Your auto-reply system is now running 24/7! 🚀**

Customers will receive instant, intelligent responses with relevant attachments based on their interests!
