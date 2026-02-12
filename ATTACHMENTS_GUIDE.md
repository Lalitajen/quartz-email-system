# Attachments Management Guide

## Overview
The Attachments page allows you to manage PDF files and assign them to different pipeline stages through an easy-to-use web interface.

## Access the Page
Navigate to: **http://localhost:5000/attachments**

Or click **"Attachments"** in the navigation bar.

---

## Features

### 1. **View Current Configuration**
See which PDF files are attached to each of the 7 pipeline stages:

- **Stage 1 - Prospecting**: Initial cold outreach
- **Stage 2 - Initial Contact**: Customer showed interest
- **Stage 3 - Qualification**: Technical evaluation
- **Stage 4 - Sample & Testing**: Sample requests
- **Stage 5 - Negotiation**: Pricing discussions
- **Stage 6 - Contract**: Agreement finalization
- **Stage 7 - Fulfillment**: Order delivery

Each stage card shows:
- ✅ Current attachments (green badge = file exists, red = missing)
- 🔑 Trigger keywords for automatic progression
- ✏️ Edit button to change attachments

---

### 2. **Upload New PDF Files**

**Steps:**
1. Click **"Upload New PDF"** button (top right)
2. Select your PDF file (max 25 MB)
3. Click **"Upload"**
4. File is saved to `/attachments/` folder

**Supported:** PDF files only
**Examples:** Product brochures, technical sheets, contracts, COAs, etc.

---

### 3. **Edit Stage Attachments**

**Steps:**
1. Click **"Edit"** button on any stage card
2. Hold **Ctrl** (Windows) or **Cmd** (Mac) to select multiple PDFs
3. Click **"Save Changes"**
4. Changes are saved permanently to `config/pipeline_config.json`

**Note:** You can assign:
- **0 attachments** (no files sent)
- **1 attachment** (single PDF)
- **Multiple attachments** (several PDFs in one email)

The same PDF can be used across multiple stages.

---

### 4. **Manage PDF Files**

The **Available PDF Files** table shows all PDFs in your library:

| Column | Description |
|--------|-------------|
| **Filename** | Name of the PDF file |
| **Size** | File size in KB |
| **Last Modified** | When the file was last updated |
| **Usage** | Which stages use this file |
| **Actions** | Download or delete the file |

**Actions:**
- 🔽 **Download**: Save a copy of the PDF
- 🗑️ **Delete**: Remove the PDF (with confirmation)

---

## Current Configuration

Based on your uploaded PRD, here's the default setup:

| Stage | Attachments |
|-------|-------------|
| 1. Prospecting | `01_Brochure.pdf` |
| 2. Initial Contact | `01_Brochure.pdf`, `02_Technical_Data_Sheet.pdf` |
| 3. Qualification | `02_Technical_Data_Sheet.pdf`, `04_Detailed_Brochure.pdf` |
| 4. Sample & Testing | `02_Technical_Data_Sheet.pdf`, `Sample_Request_Form.pdf` |
| 5. Negotiation | `03_Quotation.pdf` (personalized) |
| 6. Contract | `Contract_Template.pdf`, `03_Quotation.pdf` |
| 7. Fulfillment | `COA.pdf`, `Shipping_Docs.pdf` |

---

## How Email Attachments Work

### Automatic Attachment
When you send an email to a customer:

1. System checks their **current pipeline stage**
2. Looks up which PDFs are assigned to that stage
3. **Automatically attaches** those files to the email
4. Sends the email with correct attachments

### Example Flow:
```
Customer: ABC Glass Manufacturing
Pipeline Stage: 3 - Qualification
Current Attachments: 02_Technical_Data_Sheet.pdf, 04_Detailed_Brochure.pdf

→ Email is sent with both PDFs automatically attached
```

---

## Trigger Keywords

Each stage has **trigger keywords** that help the AI automatically suggest stage progression.

**How it works:**
1. Customer replies to your email
2. AI analyzes their response
3. If it detects trigger keywords → suggests moving to next stage
4. You approve → customer moves, new attachments apply

**Example:**
- Customer at **Stage 2 - Initial Contact**
- They reply: *"Can you send the **boron** content and **ICP-MS** data?"*
- AI detects keywords: "boron", "ICP-MS"
- Suggests moving to **Stage 3 - Qualification**
- New attachments: Technical sheet + Detailed brochure

---

## Customization Examples

### Scenario 1: Add a New Product Catalog
```
1. Create your PDF: "2025_Product_Catalog.pdf"
2. Upload via Attachments page
3. Edit Stage 2 (Initial Contact)
4. Add "2025_Product_Catalog.pdf" to the list
5. Save → Now Stage 2 emails include 3 PDFs
```

### Scenario 2: Replace Quotation Template
```
1. Upload new file: "03_Quotation_Updated.pdf"
2. Edit Stage 5 (Negotiation)
3. Remove old "03_Quotation.pdf"
4. Add "03_Quotation_Updated.pdf"
5. Save → All future negotiation emails use new template
```

### Scenario 3: Remove All Attachments from a Stage
```
1. Edit the stage (e.g., Stage 1)
2. Deselect all PDFs (click while holding Ctrl/Cmd)
3. Save → Emails sent at this stage have no attachments
```

---

## File Persistence

### Temporary (In-Memory)
If you edit attachments **without restarting the app**, changes are stored in memory only.

### Permanent (Saved to Disk)
When you click **"Save Changes"**, the configuration is written to:
```
/config/pipeline_config.json
```

This file is loaded on every app startup, so your changes **persist across restarts**.

---

## Troubleshooting

### ❌ Red Badge on Stage Card
**Problem:** File is assigned but doesn't exist
**Solution:** Upload the missing PDF or remove it from the stage

### ⚠️ "File not found" when downloading
**Problem:** PDF was deleted from disk
**Solution:** Re-upload the file

### 📧 Emails sent without attachments
**Problem:** Stage has no PDFs assigned
**Solution:** Edit the stage and add PDF files

### 🔄 Changes don't persist after restart
**Problem:** Config file wasn't saved
**Solution:** Check that `config/pipeline_config.json` exists

---

## Best Practices

### ✅ Do:
- Keep PDF files under 10 MB for faster email delivery
- Use descriptive filenames (e.g., "Technical_Datasheet_2025.pdf")
- Test emails to yourself before sending to customers
- Regularly review which files are used/unused
- Update PDFs when product specs change

### ❌ Don't:
- Upload non-PDF files (only .pdf accepted)
- Delete files that are currently assigned to stages
- Use special characters in filenames (@, #, %, etc.)
- Upload files larger than 25 MB (Gmail limit)

---

## GDPR/CAN-SPAM Compliance

All generated PDFs include a compliance footer:

```
This email was sent by Lorh La Seng Commercial Sole Company Limited,
Borikhamxay Province, Lao PDR.

If you wish to unsubscribe from future communications, please reply
with "UNSUBSCRIBE" in the subject line. We respect your privacy and
comply with GDPR and CAN-SPAM regulations.
```

This footer ensures your outbound emails comply with:
- 🇪🇺 **GDPR** (EU Data Protection Regulation)
- 🇺🇸 **CAN-SPAM Act** (US Email Law)

---

## API Reference

For programmatic access:

```bash
# Upload PDF
POST /attachments/upload
Form-data: pdf_file=@yourfile.pdf

# Update stage attachments
POST /attachments/update-stage
Form-data: stage_number=3&attachments=file1.pdf&attachments=file2.pdf

# Download PDF
GET /attachments/download/filename.pdf

# Delete PDF
POST /attachments/delete/filename.pdf
```

---

## Summary

The **Attachments Management** page gives you complete control over your email automation:

1. ✅ **Visual Interface** - See all stages and attachments at a glance
2. ✅ **Easy Uploads** - Drag and drop PDF files
3. ✅ **Flexible Assignment** - Mix and match files across stages
4. ✅ **Automatic Email Attachment** - No manual work needed
5. ✅ **Persistent Storage** - Changes saved permanently

**Your outreach is now fully automated with the right materials at every stage!**

---

**Need help?** Check the web app at http://localhost:5000/attachments or contact support.
