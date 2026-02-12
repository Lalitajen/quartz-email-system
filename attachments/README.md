# Email Attachments

This folder contains PDF attachments that will be sent with emails at each pipeline stage.

## Files Required

Replace the placeholder files with your actual PDF documents:

### Stage 1: Prospecting
- **01_Brochure.pdf** - Company brochure introducing your quartz products

### Stage 2: Initial Contact
- **01_Brochure.pdf** - Same brochure from Stage 1
- **02_Technical_Data_Sheet.pdf** - Technical specifications and purity data

### Stage 3: Qualification
- **02_Technical_Data_Sheet.pdf** - Same technical sheet
- **04_Detailed_Brochure.pdf** - More detailed product information with ICP-MS data

### Stage 4: Sample & Testing
- **02_Technical_Data_Sheet.pdf** - Same technical sheet
- **Sample_Request_Form.pdf** - Form for customers to request 2-5kg samples

### Stage 5: Negotiation
- **03_Quotation.pdf** - Personalized quotation (will be generated/customized per customer)

### Stage 6: Contract
- **Contract_Template.pdf** - Standard contract template
- **03_Quotation.pdf** - Final agreed quotation

### Stage 7: Fulfillment
- **COA.pdf** - Certificate of Analysis
- **Shipping_Docs.pdf** - Shipping documentation

## Automatic Stage Progression

The system will automatically detect when a customer's reply contains trigger keywords and suggest moving them to the next stage:

- **Stage 1→2**: interested, more info, specifications
- **Stage 2→3**: purity, SiO2, boron, specifications, ICP-MS
- **Stage 3→4**: sample, trial, test, 2-5kg, lab
- **Stage 4→5**: price, quote, quotation, cost, FOB, CIF, volume
- **Stage 5→6**: contract, agreement, terms, payment
- **Stage 6→7**: delivery, shipping, invoice, COA

## Instructions

1. Replace each placeholder PDF with your actual document
2. Keep the exact file names as listed above
3. Ensure all PDFs are under 25MB (Gmail attachment limit)
4. Test by sending a test email to yourself first
