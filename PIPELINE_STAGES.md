# Quartz Email Outreach - Pipeline Stages Configuration

## Overview
The system automatically manages email attachments and stage progression based on customer responses.

---

## Stage 1: Prospecting
**Purpose**: Cold outreach and introduction

**Attachments**:
- 01_Brochure.pdf

**Next Stage Triggers**: Customer replies with keywords like:
- "interested"
- "more info"
- "specifications"

---

## Stage 2: Initial Contact
**Purpose**: Customer has shown interest, provide detailed information

**Attachments**:
- 01_Brochure.pdf
- 02_Technical_Data_Sheet.pdf

**Next Stage Triggers**: Customer asks about technical details:
- "purity"
- "SiO2"
- "boron"
- "specifications"
- "ICP-MS"

---

## Stage 3: Qualification
**Purpose**: Customer is evaluating technical requirements

**Attachments**:
- 02_Technical_Data_Sheet.pdf
- 04_Detailed_Brochure.pdf

**Next Stage Triggers**: Customer requests samples:
- "sample"
- "trial"
- "test"
- "2-5kg"
- "lab"

---

## Stage 4: Sample & Testing
**Purpose**: Customer is testing your product

**Attachments**:
- 02_Technical_Data_Sheet.pdf
- Sample_Request_Form.pdf

**Next Stage Triggers**: Customer discusses pricing:
- "price"
- "quote"
- "quotation"
- "cost"
- "FOB"
- "CIF"
- "volume"

---

## Stage 5: Negotiation
**Purpose**: Pricing and terms discussion

**Attachments**:
- 03_Quotation.pdf (personalized for each customer)

**Next Stage Triggers**: Customer ready to formalize:
- "contract"
- "agreement"
- "terms"
- "payment"

---

## Stage 6: Contract
**Purpose**: Finalizing agreement

**Attachments**:
- Contract_Template.pdf
- 03_Quotation.pdf

**Next Stage Triggers**: Moving to delivery:
- "delivery"
- "shipping"
- "invoice"
- "COA"

---

## Stage 7: Fulfillment
**Purpose**: Order fulfillment and delivery

**Attachments**:
- COA.pdf (Certificate of Analysis)
- Shipping_Docs.pdf

**Next Stage**: Order complete → Return to Stage 1 for repeat orders

---

## How It Works

### Automatic Detection
The AI system analyzes customer email replies and detects trigger keywords. When keywords are found, the system:

1. ✅ Flags the customer for stage advancement
2. 📧 Prepares email with appropriate attachments for next stage
3. 🔔 Notifies you for approval before sending

### Manual Override
You can always manually move customers between stages via:
- The web dashboard
- Direct Google Sheets editing

### Personalization
The AI generates personalized email content based on:
- Customer's previous responses
- Their specific pain points (from research)
- Their industry and company size
- Current pipeline stage

---

## File Management

All attachment PDFs are stored in: `/attachments/`

**Important**:
- Keep file names exactly as specified
- Maximum file size: 25MB per attachment
- Supported format: PDF only
- Update files anytime - changes apply immediately

---

## Configuration

Pipeline stages are defined in:
`scripts/main_automation.py` → `PIPELINE_STAGES` dictionary

To modify:
1. Edit the PIPELINE_STAGES dictionary
2. Add/remove attachments or trigger keywords
3. Restart the web app
4. Changes take effect immediately

---

## Monitoring

Track pipeline progression in:
- **Web Dashboard**: Real-time stage visualization
- **Google Sheets**: "Customers" tab → "Pipeline Stage" column
- **Tracking Page**: Email history and responses

---

*Last Updated: 2026-02-08*
