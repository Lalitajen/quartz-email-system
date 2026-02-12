# Automated Email Workflow - Complete User Guide

## 🎯 System Overview

This automated system handles:
1. **Customer Segmentation** - AI analyzes engagement and categorizes customers
2. **Smart Follow-ups** - Automatically generates contextual follow-up emails
3. **Automated Sending** - Sends approved emails with proper timing
4. **Hot Lead Alerts** - Flags customers who need immediate attention
5. **Daily Reports** - Tracks all activity and metrics

---

## 🚀 Quick Start Guide

### Run the Automated Workflow

```bash
# Daily automated workflow
python scripts/automated_workflow.py
```

This single command will:
- ✅ Analyze all customer engagement levels
- ✅ Identify customers needing follow-ups
- ✅ Generate follow-up email drafts
- ✅ Alert you to HOT leads
- ✅ Send approved emails
- ✅ Generate daily report

**Run this once daily** (morning is best)

---

## 📊 What Happens When You Run It

### Phase 1: Customer Segmentation (2-5 minutes)
```
🔍 Analyzing: ABC Semiconductors
   Level: HOT | Intent: high | Urgency: 9/10

🔍 Analyzing: XYZ Optics Ltd  
   Level: WARM | Intent: medium | Urgency: 6/10

🔍 Analyzing: Solar Tech Industries
   Level: INTERESTED | Intent: low | Urgency: 3/10
```

**What it does:**
- Reads customer data and email history from Google Sheets
- Uses AI to analyze each customer's engagement
- Assigns engagement level (HOT/WARM/INTERESTED/COLD/UNRESPONSIVE)
- Calculates urgency score (1-10)
- Updates customer records with analysis

**Updates in Google Sheets → Customers tab:**
- Column: `engagement_level`
- Column: `buying_intent`
- Column: `urgency_score`
- Column: `next_action`
- Column: `last_analyzed`

---

### Phase 2: Identify Follow-ups (1-3 minutes)
```
📨 ABC Semiconductors - Opened but no reply (3 days ago)
   ✅ Follow-up queued for review

📨 XYZ Optics Ltd - Not opened (5 days ago)
   ✅ Follow-up queued for review
```

**What it does:**
- Scans all customers to find who needs follow-up
- Determines follow-up timing based on engagement level
- AI generates contextual follow-up email for each
- Adds drafts to Email_Tracking sheet with status "pending_review"

**Creates in Google Sheets → Email_Tracking tab:**
- New rows with `status = queued`
- Column: `reviewed_by = pending_review`
- Includes AI-generated subject and body
- Shows recommended attachments

---

### Phase 3: Process HOT Leads (<1 minute)
```
🔥 HOT: ABC Semiconductors
   Urgency: 9/10
   Action: Send detailed quotation immediately

🔥 HOT: Global Silicon Corp
   Urgency: 10/10
   Action: Schedule call today
```

**What it does:**
- Identifies all customers marked as HOT
- Creates alert entries for immediate attention
- Logs to dedicated Hot_Leads_Alert sheet

**Creates in Google Sheets → Hot_Leads_Alert tab:**
- Customer details
- Urgency score
- Recommended immediate action
- Alert timestamp

**⚠️ CHECK THIS FIRST** - These need same-day attention!

---

### Phase 4: Send Approved Emails (2-10 minutes)
```
✅ Email sent to john.smith@abcsemi.com
✅ Email sent to sarah@xyzoptics.com
✅ Email sent to mike@solartech.com
```

**What it does:**
- Finds emails you've approved (reviewed_by = "approved")
- Sends via Gmail API
- Attaches relevant files
- Updates status to "sent"
- Adds timestamp

**Sends emails where:**
- Status: `queued`
- Reviewed_by: `approved` (you changed from "pending_review")

**Updates in Email_Tracking:**
- Status: `sent`
- Sent_time: actual timestamp
- Reviewed_by: `auto_sent`

---

### Phase 5: Daily Report (<1 minute)
```
📊 Today's Summary:
   Customers: 247
   HOT Leads: 12 🔥
   WARM Leads: 45
   Emails Sent: 18
   Replies: 5
   Response Rate: 27.8%
   Pending Reviews: 8
```

**What it does:**
- Calculates key metrics for the day
- Logs to Daily_Reports sheet
- Displays summary in terminal

**Creates in Google Sheets → Daily_Reports tab:**
- Date
- All key metrics
- Response rates
- Pending actions

---

## 📋 Your Daily Workflow

### Morning Routine (15-20 minutes)

#### Step 1: Run Automation
```bash
python scripts/automated_workflow.py
```

Wait for completion (5-10 minutes)

---

#### Step 2: Check HOT Leads FIRST
1. Open Google Sheets
2. Go to **Hot_Leads_Alert** tab
3. Review all entries with `status = needs_attention`

**For each HOT lead:**
```
☑️ Read urgency score and recommended action
☑️ Check their email history in Email_Tracking
☑️ Review their customer profile in Customers
☑️ Take immediate action:
   - Call them if urgency 8-10
   - Send personalized email if urgency 6-7
   - Prepare detailed quotation
```

**Mark handled:**
Change `status` to `contacted` after taking action

---

#### Step 3: Review Pending Follow-ups
1. Go to **Email_Tracking** tab
2. Filter: `reviewed_by = pending_review`
3. Sort by `urgency_score` (if column exists)

**For each pending email:**

**Option A: Approve as-is**
```
✅ Read subject and body
✅ Verify it sounds appropriate
✅ Check attachments are correct
✅ Change reviewed_by to: "approved"
```

**Option B: Edit before approving**
```
✏️ Click on body cell
✏️ Make your edits
✏️ Adjust subject if needed
✏️ Change reviewed_by to: "approved"
```

**Option C: Reject**
```
❌ Not appropriate or not needed
❌ Change reviewed_by to: "rejected"
❌ Add note in a comment if you want
```

---

#### Step 4: Check Dashboard
1. Go to **Dashboard** tab
2. Review key metrics:
   - Response rate trend
   - Pipeline distribution
   - Pending actions

---

### Afternoon Check (5 minutes)

#### Check for New Replies
The system monitors Gmail, but you can also:

1. Check your Gmail inbox
2. Look for replies from customers in your pipeline
3. System will detect these in next run, but you can respond manually if urgent

---

### End of Day (5 minutes)

#### Review Daily Report
1. Go to **Daily_Reports** tab
2. Check today's row
3. Note any trends or issues

#### Plan Tomorrow
- Note any urgent follow-ups needed
- Schedule calls with HOT leads
- Prepare materials for key prospects

---

## 🎛️ Control Panel (Google Sheets)

### Sheet Overview

```
📊 Customers
   → Main customer database
   → Engagement levels updated here
   → Check "engagement_level" column
   
📧 Email_Tracking  
   → All sent/queued emails
   → Review "pending_review" items here
   → Change to "approved" to send
   
🔥 Hot_Leads_Alert
   → High-priority customers
   → CHECK THIS FIRST every day
   → Needs same-day attention
   
📈 Dashboard
   → Real-time metrics
   → Pipeline visualization
   → Key performance indicators
   
📋 Daily_Reports
   → Historical tracking
   → Trend analysis
   → Activity logs
```

---

## ✅ Approval Process

### How to Approve Emails for Sending

**Method 1: Direct Approval (Quick)**
```
1. Open Email_Tracking sheet
2. Find rows with reviewed_by = "pending_review"
3. Read the email content
4. If good → Change reviewed_by to: "approved"
5. Next run will send it automatically
```

**Method 2: Edit First (Careful)**
```
1. Find pending email row
2. Click on "body" cell
3. Edit the text as needed
4. Edit "subject" if needed
5. Check "attachments" column
6. Change reviewed_by to: "approved"
```

**Method 3: Reject**
```
1. Find pending email row
2. Change reviewed_by to: "rejected"
3. System will skip it
```

---

## 🔄 Automated Follow-up Logic

### When System Creates Follow-ups:

**Scenario 1: No Response**
```
Customer: Sent email 3 days ago
Status: Delivered, but no reply
Action: Generate gentle follow-up
Timing: Automatically queued for today
```

**Scenario 2: Opened But No Reply**
```
Customer: Opened email 2 days ago
Status: Engaged but didn't respond
Action: Generate value-add follow-up
Timing: Automatically queued for today
```

**Scenario 3: Multiple Engagements**
```
Customer: Opened 3 times, no reply
Status: Very interested but hesitant
Action: Generate offer-based follow-up
Timing: Automatically queued for today
```

---

## 🎯 Engagement-Based Actions

### System automatically adjusts based on engagement:

**HOT (Priority 1)**
```
Follow-up: Next day
Message: Personalized, solution-focused
Attachments: Detailed quotation, case study
Your Action: Call or personal email same day
```

**WARM (Priority 2)**
```
Follow-up: 3 days
Message: Educational, value-add
Attachments: Technical specs, whitepaper
Your Action: Review and approve automated email
```

**INTERESTED (Priority 3)**
```
Follow-up: 5 days
Message: Social proof, alternative angle
Attachments: Testimonials, certifications
Your Action: Review and approve automated email
```

**COLD (Priority 4)**
```
Follow-up: 7 days
Message: Re-engagement, create urgency
Attachments: Special offer, one-pager
Your Action: Consider different approach
```

**UNRESPONSIVE (Priority 5)**
```
Follow-up: Paused (90 days later)
Message: Break-up email or archive
Attachments: None
Your Action: Focus on active leads
```

---

## 📊 Interpreting Customer Data

### Key Columns in Customers Sheet:

**engagement_level**
- Shows: HOT/WARM/INTERESTED/COLD/UNRESPONSIVE
- Updated: Every workflow run
- Use: Prioritize your time

**buying_intent**
- Shows: high/medium/low/none
- Updated: Every workflow run
- Use: Gauge sales probability

**urgency_score**
- Shows: 1-10
- 10 = Needs immediate attention
- 1 = Low priority
- Use: Prioritize actions

**next_action**
- Shows: AI recommendation
- Examples: "Send quotation", "Schedule call"
- Use: Know what to do next

**last_analyzed**
- Shows: When AI last analyzed
- Use: Ensure data is fresh

---

## 🔧 Customization Options

### Adjust Follow-up Timing

Edit `automated_workflow.py`:
```python
# Line ~150
ENGAGEMENT_LEVELS = {
    'HOT': {
        'follow_up_days': 1,  # Change this
    },
    'WARM': {
        'follow_up_days': 3,  # Change this
    },
    # etc.
}
```

### Adjust Segmentation Criteria

Edit the AI prompt in `CustomerSegmentationEngine`:
```python
# Line ~85
# Modify the prompt to emphasize different signals
```

### Change Email Tone

Edit the prompt in `FollowUpManager.generate_follow_up_email()`:
```python
# Line ~230
# Adjust the prompt instructions for tone/style
```

---

## 🐛 Troubleshooting

### Issue: Emails not sending
**Check:**
- [ ] Gmail authentication completed (token.json exists)
- [ ] Email has reviewed_by = "approved"
- [ ] Email status = "queued" (not "sent")
- [ ] Valid email address in contact_email

**Fix:**
```bash
# Re-authenticate Gmail
rm token.json
python scripts/automated_workflow.py
# Browser will open for OAuth
```

---

### Issue: No follow-ups generated
**Check:**
- [ ] Customers have email history
- [ ] Enough days passed since last email
- [ ] Customer not marked as UNRESPONSIVE

**Fix:**
- Manually add test emails to Email_Tracking
- Verify date formats are correct (YYYY-MM-DD)

---

### Issue: Customer segmentation not updating
**Check:**
- [ ] Google Sheets authentication working
- [ ] Anthropic API key valid
- [ ] Sufficient email history for analysis

**Fix:**
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test sheets connection
python -c "from scripts.automated_workflow import GoogleSheetsManager; 
m = GoogleSheetsManager('YOUR_SHEETS_ID'); 
m.authenticate(); 
print('Connected!')"
```

---

## 📈 Success Metrics

### Daily Goals:
- ✅ All HOT leads contacted within 24 hours
- ✅ All pending emails reviewed
- ✅ Response rate >10%
- ✅ No emails sitting >3 days unreviewed

### Weekly Goals:
- ✅ Convert 20% of WARM to HOT
- ✅ Convert 30% of HOT to Quotation
- ✅ Response rate >12%
- ✅ Clean up UNRESPONSIVE leads

### Monthly Goals:
- ✅ 50+ new customers in pipeline
- ✅ 10+ quotations sent
- ✅ 5+ samples shipped
- ✅ Response rate >15%

---

## 💡 Pro Tips

### Maximize Efficiency:
1. **Run automation first thing** → Let AI do the analysis while you prep
2. **HOT leads first, always** → These are your money makers
3. **Batch review emails** → Approve 10-20 at once
4. **Trust the AI, but verify** → AI is 80-90% accurate, quick review adds human touch
5. **Track what works** → Note which emails get best responses

### Avoid Common Mistakes:
1. ❌ Don't ignore HOT lead alerts
2. ❌ Don't send without reviewing (at least skim)
3. ❌ Don't let pending reviews pile up
4. ❌ Don't forget to update status after calling HOT leads
5. ❌ Don't send generic emails to HOT leads

### Advanced Tactics:
1. ✅ Combine email with LinkedIn connection
2. ✅ Send video message to HOT leads
3. ✅ Create custom attachments for key prospects
4. ✅ A/B test subject lines manually
5. ✅ Call HOT leads before emailing

---

## 🎓 Training Your Team

### For Sales Team:
- Focus on HOT lead follow-up
- Review and approve automated emails
- Customize key prospect messages
- Track conversion metrics

### For Operations:
- Run daily automation
- Monitor system health
- Update customer data
- Generate weekly reports

### For Management:
- Review Dashboard
- Check Daily_Reports
- Analyze trends
- Adjust strategy

---

## 📞 Quick Reference

### Daily Commands:
```bash
# Run full workflow
python scripts/automated_workflow.py

# Just check for replies
python scripts/main_automation.py

# Setup dashboard (one-time)
python scripts/dashboard_setup.py YOUR_SHEETS_ID
```

### Google Sheets Tabs:
- **Customers** → Customer database + engagement
- **Email_Tracking** → All emails (pending + sent)
- **Hot_Leads_Alert** → Priority actions
- **Dashboard** → Metrics overview
- **Daily_Reports** → Historical data

### Key Status Values:
- `pending_review` → Needs your approval
- `approved` → Will send on next run
- `rejected` → Won't send
- `sent` → Already sent
- `queued` → Approved, waiting to send

---

You now have a complete intelligent email automation system that works for you 24/7! Focus your time on high-value activities (HOT leads, closing deals) while automation handles research, follow-ups, and tracking.
