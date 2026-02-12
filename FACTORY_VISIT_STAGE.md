# 🏭 Factory Visit Stage - Stage 10

## Overview
Added new pipeline stage for customers who want to visit the factory facility in Laos. The system now automatically detects factory visit requests and sends appropriate information.

## Stage Details

**Stage Number:** 10
**Stage Name:** Factory Visit
**Color:** Blue (#007bff)

## PDF Attachments

When a customer mentions visiting the factory, the system automatically sends:

1. **Factory_Tour_Info.pdf** (586 bytes)
   - Factory visit details
   - Location: Vientiane Capital, Laos
   - Production capacity information
   - Tour duration and schedule
   - What customers will see during the visit
   - Contact information

2. **Company_Profile.pdf** (691 bytes)
   - Company background
   - Key capabilities and certifications
   - Production specifications
   - Export markets and applications
   - Management information
   - Contact details

3. **Location_Directions.pdf** (787 bytes)
   - Factory address with GPS coordinates
   - Directions from Vientiane city center
   - Directions from Wattay International Airport
   - Nearby landmarks
   - Export port information
   - Visit arrangement instructions

## Trigger Keywords

The AI will detect Stage 10 when customers use these keywords:

- `visit`
- `factory`
- `tour`
- `facility`
- `inspection`
- `audit`
- `see`
- `plant`
- `production`
- `meet`
- `location`
- `address`
- `directions`

## Example Customer Emails

### Example 1:
```
Subject: Request for Factory Visit

We would like to visit your factory facility next month to see
the production process and meet with your technical team.
```
**AI Response:** Stage 10 → Sends Factory Tour Info + Company Profile + Location Directions

### Example 2:
```
Subject: Factory Inspection

We need to conduct a factory audit and inspection of your
production facility. Can you provide the factory location?
```
**AI Response:** Stage 10 → Sends Factory Tour Info + Company Profile + Location Directions

### Example 3:
```
Subject: Plant Tour

I'll be visiting Laos next month and would like to schedule
a tour of your quartz production plant.
```
**AI Response:** Stage 10 → Sends Factory Tour Info + Company Profile + Location Directions

## How to Test

Run the test script to verify Stage 10 works correctly:

```bash
python3 test_factory_visit_stage.py
```

This will:
1. Send a test email requesting a factory visit
2. Trigger the auto-reply daemon
3. Send back the 3 factory visit PDFs
4. You'll receive the response in ~5-45 seconds

## Updated Pipeline Stages

The system now has **10 complete stages**:

| Stage | Name | Attachments |
|-------|------|-------------|
| 1 | Prospecting | 01_Brochure.pdf |
| 2 | Initial Contact | 01_Brochure.pdf, 02_Technical_Data_Sheet.pdf |
| 3 | Qualification | 02_Technical_Data_Sheet.pdf, 04_Detailed_Brochure.pdf |
| 4 | Sample & Testing | 02_Technical_Data_Sheet.pdf, Sample_Request_Form.pdf |
| 5 | Negotiation | 03_Quotation.pdf |
| 6 | Contract | Contract_Template.pdf, 03_Quotation.pdf |
| 7 | Fulfillment | COA.pdf, Shipping_Docs.pdf |
| 8 | Follow-Up & Satisfaction | Customer_Satisfaction_Survey.pdf |
| 9 | Repeat Customer | VIP_Discount_Program.pdf, Bulk_Order_Benefits.pdf |
| **10** | **Factory Visit** | **Factory_Tour_Info.pdf, Company_Profile.pdf, Location_Directions.pdf** |

## Web Interface

The Auto-Reply Monitor page at http://localhost:5000/auto-reply now shows:

- **Stage 10 card** with blue border
- **PDF attachments** listed with file icons
- **Trigger keywords** preview
- **Email count** for Stage 10 when emails are processed

## Files Modified

1. **auto_reply_daemon.py** - Added Stage 10 to PIPELINE_STAGES
2. **scripts/web_app.py** - Added Stage 10 to web interface
3. **scripts/auto_reply_enhanced.py** - Added .stage-card-10 CSS style

## Files Created

1. **attachments/Factory_Tour_Info.pdf** - Factory tour details
2. **attachments/Company_Profile.pdf** - Company background
3. **attachments/Location_Directions.pdf** - Factory location and directions
4. **test_factory_visit_stage.py** - Test script for Stage 10

## System Status

✅ Auto-Reply Daemon restarted with Stage 10 support
✅ 3 new PDF attachments created
✅ Web interface updated with Stage 10 card
✅ Test script ready for validation

## Next Steps

1. **Test the new stage:**
   ```bash
   python3 test_factory_visit_stage.py
   ```

2. **Monitor the results:**
   ```bash
   tail -f /tmp/auto_reply.log
   ```

3. **View in web interface:**
   ```bash
   python3 scripts/web_app.py
   # Open: http://localhost:5000/auto-reply
   ```

---

**Stage 10 is now LIVE and monitoring for factory visit requests 24/7!** 🏭✨
