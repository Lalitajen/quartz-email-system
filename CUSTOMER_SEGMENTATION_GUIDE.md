# Customer Segmentation & Automated Actions Guide

## 🎯 Customer Engagement Levels

Your system automatically segments customers into 5 levels based on their behavior and engagement:

---

## 🔥 HOT Leads (Priority 1)

### Identification Criteria:
- ✅ Replied to multiple emails
- ✅ Requested quotation or pricing
- ✅ Requested sample shipment
- ✅ Asked for meeting/call
- ✅ Showed strong buying signals

### Automated Actions:
1. **Immediate Alert** → Added to Hot_Leads_Alert sheet
2. **Urgency Score** → 8-10/10
3. **Follow-up Time** → Within 24 hours
4. **Recommended Action** → Personal phone call + detailed quotation

### What to Send:
```
EMAIL TYPE: Personalized Quotation + Sample Offer
ATTACHMENTS: 
- Detailed quotation (personalized)
- Technical specifications
- Case study or reference
- Sample request form

TONE: Professional, responsive, solution-focused
CTA: Schedule meeting or sample shipment
```

### Example Scenario:
```
Customer: ABC Semiconductors
Signals: 
- Opened 3 emails
- Replied asking about purity levels
- Requested technical datasheet
- Asked about MOQ and pricing

Action: 
→ Move to stage 5 (Negotiation)
→ Generate personalized quotation
→ Offer sample with expedited testing
→ Propose technical call this week
```

---

## 🌡️ WARM Leads (Priority 2)

### Identification Criteria:
- ✅ Opened emails consistently
- ✅ Clicked links in email
- ✅ Replied at least once
- ✅ Asked clarifying questions
- ✅ Engaged with content

### Automated Actions:
1. **Track Engagement** → Monitor opens/clicks
2. **Urgency Score** → 5-7/10
3. **Follow-up Time** → Within 3 days
4. **Recommended Action** → Send additional value (case study, whitepaper)

### What to Send:
```
EMAIL TYPE: Educational + Value-Add Content
ATTACHMENTS:
- Industry insights report
- Customer success stories
- Technical comparison guide
- Product catalog

TONE: Helpful, informative, building trust
CTA: Answer questions or provide consultation
```

### Example Scenario:
```
Customer: XYZ Optics Ltd
Signals:
- Opened all emails
- Clicked product catalog link
- Replied with general questions
- No urgent buying signals yet

Action:
→ Stay in stage 2 (Initial Contact)
→ Send case study of similar optical company
→ Offer free consultation call
→ Follow up in 3 days if no response
```

---

## 👀 INTERESTED Leads (Priority 3)

### Identification Criteria:
- ✅ Opened at least one email
- ✅ Viewed email multiple times
- ✅ Passive engagement (no reply yet)
- ✅ Still in early stages

### Automated Actions:
1. **Nurture Campaign** → Add to educational sequence
2. **Urgency Score** → 3-5/10
3. **Follow-up Time** → Within 5 days
4. **Recommended Action** → Different angle or offer

### What to Send:
```
EMAIL TYPE: Social Proof + Alternative Angle
ATTACHMENTS:
- Customer testimonials
- Quality certifications
- Factory tour video link
- Special offer or discount

TONE: Friendly, less technical, benefit-focused
CTA: Low-commitment (download resources, watch video)
```

### Example Scenario:
```
Customer: Solar Tech Industries
Signals:
- Opened initial email twice
- No reply
- Viewed company profile attachment
- 5 days since last email

Action:
→ Stay in stage 1 (Prospecting)
→ Send different angle: sustainability focus
→ Include testimonial from solar industry client
→ Offer downloadable quality certificate
```

---

## ❄️ COLD Leads (Priority 4)

### Identification Criteria:
- ✅ Did not open initial email
- ✅ No response after 7+ days
- ✅ Minimal or no engagement
- ✅ May need different approach

### Automated Actions:
1. **Re-engagement Attempt** → Try different subject line
2. **Urgency Score** → 1-3/10
3. **Follow-up Time** → Within 7 days
4. **Recommended Action** → Break-up email or alternative contact

### What to Send:
```
EMAIL TYPE: Last Attempt / Re-engagement
ATTACHMENTS:
- One-page company overview
- Special limited-time offer
- Industry trend report

TONE: Direct, value-focused, create FOMO
CTA: Clear yes/no decision point
```

### Example Follow-up Template:
```
Subject: Should I close your file?

Hi [Name],

I haven't heard back from you regarding high-purity quartz supply, 
so I wanted to check one last time.

If now isn't the right time, no problem - I'll close your file 
and won't reach out again.

But if you're still interested, I'd love to discuss:
- 15% discount for first-time bulk orders
- Expedited sample testing
- Flexible payment terms

Just reply "YES" and I'll send details, or "NO" and I'll mark 
your file closed.

Best regards,
[Your name]
```

---

## 🚫 UNRESPONSIVE Leads (Priority 5)

### Identification Criteria:
- ✅ Multiple attempts with no engagement
- ✅ No opens, no clicks, no replies
- ✅ 3+ emails sent over 14+ days
- ✅ Dead end

### Automated Actions:
1. **Pause Campaign** → Stop sending emails
2. **Urgency Score** → 0/10
3. **Follow-up Time** → 30-90 days later
4. **Recommended Action** → Archive or try different contact

### What to Do:
```
ACTION: Remove from active campaign
REASON: Low probability, wastes time/resources
ALTERNATIVES:
- Try different email address
- Find different contact at company
- Reach out via LinkedIn
- Wait 90 days and try again with fresh angle
- Mark as "not interested" in CRM
```

---

## 📊 Automated Segmentation Workflow

```
New Customer Added
       ↓
   Send Email
       ↓
   Wait 3 Days
       ↓
[Check Engagement]
       ↓
    ┌──┴──┐
    ↓     ↓
Opened? Replied?
    │     │
    ↓     ↓
  [AI ANALYSIS]
       ↓
  ┌────┼────┐
  ↓    ↓    ↓
HOT  WARM  COLD
  │    │    │
  ↓    ↓    ↓
[AUTOMATED ACTIONS]
```

---

## 🤖 AI Analysis Determines:

1. **Engagement Level** → HOT/WARM/INTERESTED/COLD/UNRESPONSIVE
2. **Buying Intent** → high/medium/low/none
3. **Pain Points** → What they care about
4. **Next Best Action** → What to send next
5. **Urgency Score** → 1-10 priority ranking
6. **Recommended Message Type** → Template to use

---

## 📧 Automated Follow-up Timing

| Engagement Level | First Follow-up | Second Follow-up | Third Follow-up |
|-----------------|----------------|------------------|-----------------|
| HOT | 1 day | Same day if urgent | - |
| WARM | 3 days | 5 days | 10 days |
| INTERESTED | 5 days | 10 days | 15 days |
| COLD | 7 days | 14 days | Archive |
| UNRESPONSIVE | Archive | Re-engage in 90 days | - |

---

## 🎯 Pipeline Stage Transitions

System automatically suggests stage changes based on engagement:

```
INTERESTED + asking questions → Move to Stage 2 (Initial Contact)
WARM + requested specs → Move to Stage 3 (Qualification)
WARM + requested sample → Move to Stage 4 (Sample & Testing)
HOT + requested quote → Move to Stage 5 (Negotiation)
HOT + agreed terms → Move to Stage 6 (Contract)
```

---

## 📈 Measuring Success

### Key Metrics by Segment:

**HOT Leads:**
- Conversion to Quote: 70%+
- Average Deal Size: $50K+
- Time to Close: 2-4 weeks

**WARM Leads:**
- Conversion to HOT: 30%+
- Average Deal Size: $30K+
- Time to Close: 4-8 weeks

**INTERESTED Leads:**
- Conversion to WARM: 15%+
- Average Deal Size: $20K+
- Time to Close: 8-12 weeks

**COLD Leads:**
- Conversion to INTERESTED: 5%+
- Usually need alternative approach

---

## 🔄 Re-engagement Strategies

### For COLD Leads:
1. **Different Angle** → Try sustainability, cost savings, or quality focus
2. **Different Contact** → Try different person at company
3. **Different Channel** → LinkedIn message, phone call
4. **Different Timing** → Quarterly budget cycles, industry events

### For UNRESPONSIVE Leads:
1. **90-Day Reset** → Fresh start with new message
2. **LinkedIn Research** → Find warmer contact path
3. **Industry Event** → Re-engage at trade show
4. **Archive** → Focus resources on engaged leads

---

## 💡 Pro Tips

### Maximize HOT Lead Conversion:
- ✅ Respond within 1 hour
- ✅ Have quotation ready to send
- ✅ Offer video call option
- ✅ Provide multiple payment options
- ✅ Fast-track sample if needed

### Warm Up COLD Leads:
- ✅ Try different subject lines
- ✅ Mention industry-specific pain point
- ✅ Use social proof (testimonials)
- ✅ Create urgency (limited offer)
- ✅ Make it personal (custom video)

### Prevent Leads from Going Cold:
- ✅ Follow up within 24-48 hours
- ✅ Add value in every email
- ✅ Ask engaging questions
- ✅ Share relevant case studies
- ✅ Stay top of mind without being pushy

---

## 🚀 Automation Rules Summary

### System Automatically:
1. ✅ Analyzes every customer interaction
2. ✅ Assigns engagement level
3. ✅ Calculates urgency score
4. ✅ Generates appropriate follow-up email
5. ✅ Selects relevant attachments
6. ✅ Queues for your review
7. ✅ Tracks response patterns
8. ✅ Suggests pipeline stage changes
9. ✅ Alerts on HOT leads
10. ✅ Pauses unresponsive campaigns

### You Decide:
1. ✅ Approve or edit AI-generated emails
2. ✅ When to send (timing)
3. ✅ Custom messaging for key accounts
4. ✅ When to call vs email
5. ✅ Final pricing and terms

---

## 📊 Daily Review Checklist

### Morning (15 minutes):
- [ ] Check Hot_Leads_Alert sheet
- [ ] Review pending follow-ups
- [ ] Approve automated emails
- [ ] Respond to HOT leads first

### Afternoon (10 minutes):
- [ ] Check new replies
- [ ] Update engagement notes
- [ ] Schedule calls with HOT leads

### End of Day (5 minutes):
- [ ] Review dashboard metrics
- [ ] Plan tomorrow's priorities
- [ ] Update any custom actions needed

---

This segmentation system ensures you focus your time on the most promising leads while automation handles the nurturing and follow-ups!
