# Quick Start: Updating PDF Attachments

## 🎯 Common Tasks

### Task 1: Replace an Outdated PDF

**Scenario:** Your brochure is outdated, you have a new 2026 version

```
✅ DELETE OLD FILE
1. Go to: http://localhost:5000/attachments
2. Scroll to "Available PDF Files" table
3. Find "01_Brochure.pdf"
4. Click 🗑️ (trash icon)
5. Confirm deletion

✅ UPLOAD NEW FILE
6. Click "Upload New PDF" button
7. Select "01_Brochure.pdf" (new version, same name!)
8. Click Upload

DONE! All stages using it now have the new version.
```

**Important:** Use the **same filename** so you don't have to reassign it to stages!

---

### Task 2: Add a Brand New PDF

**Scenario:** You created a new Safety Certification document

```
✅ UPLOAD THE FILE
1. Go to: http://localhost:5000/attachments
2. Click "Upload New PDF"
3. Select "Safety_Certification.pdf"
4. Upload

✅ ASSIGN TO STAGES
5. Decide which stage needs it (e.g., Stage 4 - Sample & Testing)
6. Click "Edit" on Stage 4 card
7. Hold Ctrl/Cmd
8. Click "Safety_Certification.pdf" to select it
9. Click "Save Changes"

DONE! Stage 4 emails now include the certification.
```

---

### Task 3: Change Which Files Go to Each Stage

**Scenario:** You want Stage 2 to send different files

```
CURRENT STATE (Stage 2):
- 01_Brochure.pdf ✓
- 02_Technical_Data_Sheet.pdf ✓

YOU WANT:
- 01_Brochure.pdf ✓
- 04_Detailed_Brochure.pdf ✓  (NEW!)
- Remove: 02_Technical_Data_Sheet.pdf

✅ EDIT THE STAGE
1. Click "Edit" on Stage 2 card
2. You see a list of all PDFs

3. Current selections:
   [✓] 01_Brochure.pdf
   [✓] 02_Technical_Data_Sheet.pdf
   [ ] 04_Detailed_Brochure.pdf

4. Hold Ctrl/Cmd and:
   - Click "02_Technical_Data_Sheet.pdf" to deselect
   - Click "04_Detailed_Brochure.pdf" to select

5. New selections:
   [✓] 01_Brochure.pdf
   [ ] 02_Technical_Data_Sheet.pdf
   [✓] 04_Detailed_Brochure.pdf

6. Click "Save Changes"

DONE! Stage 2 now sends different files.
```

---

### Task 4: Remove All Attachments from a Stage

**Scenario:** Stage 1 (Prospecting) should have no attachments for cold emails

```
✅ CLEAR ALL FILES
1. Click "Edit" on Stage 1 card
2. Hold Ctrl/Cmd
3. Click each selected file to deselect ALL of them
4. Result: No files selected
5. Click "Save Changes"

DONE! Stage 1 emails now have no attachments.
```

---

### Task 5: Regenerate PDFs with Updated Company Info

**Scenario:** You changed your phone number or address

```
✅ UPDATE THE GENERATOR SCRIPT
1. Open: scripts/generate_pdf_templates.py
2. Edit lines 50-57:

COMPANY_NAME = "Lorh La Seng Commercial Sole Company Limited"
COMPANY_ADDRESS = "Borikhamxay Province, Lao PDR"
COMPANY_EMAIL = "jennylalita1@gmail.com"
COMPANY_PHONE = "+856 20 YOUR_NEW_PHONE"  ← Change this
WEBSITE = "www.lorhlas eng.com"
EXPORT_PORT = "Cua Lo Port, Vietnam"

3. Save the file

✅ REGENERATE ALL PDFs
4. Open Terminal/Command Prompt
5. Navigate to project folder:
   cd /Users/lalita/Downloads/quartz-email-system

6. Run generator:
   cd scripts
   python3 generate_pdf_templates.py

7. All 8 PDFs are regenerated with new info!

DONE! Your PDFs now have updated contact information.
```

---

## 🎨 Interface Layout

When you open http://localhost:5000/attachments, you see:

```
┌─────────────────────────────────────────────────────┐
│  📎 Attachment Management    [Upload New PDF] ←─────┤ Click here to upload
└─────────────────────────────────────────────────────┘

┌─ Pipeline Stages & Attachments ─────────────────────┐
│                                                      │
│  ┌─ Stage 1: Prospecting ──────────────┐ [Edit] ←──┤ Click to change files
│  │ Attachments: ✓ 01_Brochure.pdf      │            │
│  │ Keywords: cold outreach, intro...   │            │
│  └──────────────────────────────────────┘            │
│                                                      │
│  ┌─ Stage 2: Initial Contact ──────────┐ [Edit]    │
│  │ Attachments: ✓ 01_Brochure.pdf      │            │
│  │              ✓ 02_Technical...       │            │
│  └──────────────────────────────────────┘            │
│  ... (7 stages total)                               │
└─────────────────────────────────────────────────────┘

┌─ Available PDF Files ───────────────────────────────┐
│                                                      │
│  Filename              Size    Modified    Actions  │
│  01_Brochure.pdf      4.2KB   2026-02-08  🔽 🗑️ ←──┤ Download / Delete
│  02_Technical...      4.4KB   2026-02-08  🔽 🗑️     │
│  03_Quotation.pdf     4.0KB   2026-02-08  🔽 🗑️     │
│  ... (8 files)                                       │
└─────────────────────────────────────────────────────┘
```

---

## ⌨️ Keyboard Shortcuts

| Action | Windows | Mac |
|--------|---------|-----|
| **Select multiple files** | Hold **Ctrl** + Click | Hold **Cmd** + Click |
| **Select all files** | Hold **Ctrl** + A (in modal) | Hold **Cmd** + A |
| **Deselect file** | Hold **Ctrl** + Click selected | Hold **Cmd** + Click |

---

## 💡 Pro Tips

### ✅ Keep Same Filenames
When updating a PDF, use the **same filename** to avoid reassigning to stages.

**Example:**
```
OLD: 01_Brochure.pdf
NEW: 01_Brochure.pdf  ← Same name!

Result: No need to edit stages, it just works!
```

### ✅ Version Your Files
For major updates, add dates to filenames:

```
❌ Bad:  Brochure.pdf, Brochure_new.pdf, Brochure_final.pdf
✅ Good: 01_Brochure_Jan2026.pdf, 01_Brochure_Feb2026.pdf
```

### ✅ Test Before Deleting
Download a backup before deleting:
1. Click 🔽 download icon
2. Save to Desktop as backup
3. Then delete and upload new version

### ✅ Check File Size
Keep PDFs under **10 MB** for email delivery:
- Over 10 MB = Slow sending
- Over 25 MB = Gmail will reject

Compress large PDFs at: smallpdf.com or ilovepdf.com

---

## ❓ Troubleshooting

### Problem: "Can't see my uploaded file"
**Solution:** Refresh the page (F5 or Cmd+R)

### Problem: "File shows red ❌ badge on stage"
**Solution:**
1. File is assigned but doesn't exist
2. Upload the missing PDF
3. Or remove it from the stage

### Problem: "Changes don't save after restart"
**Solution:**
1. Check that `config/pipeline_config.json` exists
2. If not, your changes weren't saved
3. Re-edit stages and save again

### Problem: "Upload button doesn't work"
**Solution:**
1. Make sure file is **.pdf** format
2. File size must be < 25 MB
3. Check browser console for errors

---

## 📞 Need More Help?

- **Web Interface:** http://localhost:5000/attachments
- **Full Guide:** ATTACHMENTS_GUIDE.md
- **Pipeline Info:** PIPELINE_STAGES.md
- **Project Root:** /Users/lalita/Downloads/quartz-email-system

---

**You're all set! The Attachments page gives you full control over your PDF files. No coding required!** 🎉
