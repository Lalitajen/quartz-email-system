"""
Generate PDF templates for Quartz Email Outreach System
Creates professional templates for all pipeline stages
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.platypus.flowables import HRFlowable
from datetime import datetime
import os

# Ensure attachments directory exists
os.makedirs('../attachments', exist_ok=True)

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#1a237e'),
    spaceAfter=30,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=16,
    textColor=colors.HexColor('#283593'),
    spaceAfter=12,
    spaceBefore=12,
    fontName='Helvetica-Bold'
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['BodyText'],
    fontSize=11,
    alignment=TA_JUSTIFY,
    spaceAfter=12
)

# Company branding
COMPANY_NAME = "Lorh La Seng Commercial Sole Company Limited"
COMPANY_ADDRESS = "Borikhamxay Province, Lao PDR"
COMPANY_EMAIL = "jennylalita1@gmail.com"
COMPANY_PHONE = "+856 20 [Your Phone]"
WEBSITE = "www.lorhlas eng.com"
EXPORT_PORT = "Cua Lo Port, Vietnam"
LICENSE_NO = "001-25/PKB (Apr 2025 - Apr 2030)"

def add_header(elements, doc_title):
    """Add company header to document"""
    elements.append(Paragraph(COMPANY_NAME, title_style))
    elements.append(Paragraph(f"<i>{COMPANY_ADDRESS}</i>",
                             ParagraphStyle('center', parent=styles['Normal'], alignment=TA_CENTER)))
    elements.append(Paragraph(f"<i>{COMPANY_EMAIL} | {COMPANY_PHONE} | Export: {EXPORT_PORT}</i>",
                             ParagraphStyle('center', parent=styles['Normal'], alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a237e')))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(doc_title, heading_style))
    elements.append(Spacer(1, 0.2*inch))

def add_compliance_footer(elements):
    """Add GDPR/CAN-SPAM compliance footer"""
    elements.append(Spacer(1, 0.2*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    elements.append(Spacer(1, 0.1*inch))
    compliance_text = f"""<font size=8 color="#666666">
    This email was sent by {COMPANY_NAME}, {COMPANY_ADDRESS}.
    If you wish to unsubscribe from future communications, please reply with "UNSUBSCRIBE" in the subject line.
    We respect your privacy and comply with GDPR and CAN-SPAM regulations.
    </font>"""
    elements.append(Paragraph(compliance_text,
                             ParagraphStyle('compliance', parent=styles['Normal'],
                                          alignment=TA_CENTER, fontSize=7)))

def create_brochure():
    """01_Brochure.pdf - Company introduction"""
    doc = SimpleDocTemplate("../attachments/01_Brochure.pdf", pagesize=letter)
    elements = []

    add_header(elements, "High-Purity Quartz Products")

    elements.append(Paragraph("<b>About Our Company</b>", heading_style))
    elements.append(Paragraph(
        """We are a leading supplier of high-purity quartz materials, specializing in ultra-pure
        quartz products for semiconductor, solar, optical fiber, and specialty glass industries.
        With decades of experience in mineral processing and purification, we deliver consistent
        quality that meets the most demanding specifications.""", body_style))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Our Products</b>", heading_style))

    products_data = [
        ['Product Grade', 'Purity (SiO₂)', 'Applications'],
        ['Grade A - Premium', '99.5-99.89%', 'Optical fiber, solar panels, specialty glass'],
        ['Grade B - Standard', '99.0-99.49%', 'Glass manufacturing, ceramics, refractories'],
        ['Grade C - Industrial', '98.8-98.99%', 'Construction, foundries, filtration'],
        ['Custom Processing', 'Per specification', 'Contact for custom requirements']
    ]

    table = Table(products_data, colWidths=[2.2*inch, 1.8*inch, 2.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Why Choose Lorh La Seng?</b>", heading_style))
    elements.append(Paragraph("✓ <b>Ultra-Low Boron:</b> 34.6 ppb - Semiconductor grade quality", body_style))
    elements.append(Paragraph("✓ <b>Low Iron Content:</b> 0.24-0.30 ppm - Exceptional optical clarity", body_style))
    elements.append(Paragraph("✓ <b>Large Capacity:</b> 30,000-50,000 tons/month production", body_style))
    elements.append(Paragraph("✓ <b>Strategic Location:</b> Export via Cua Lo Port, Vietnam", body_style))
    elements.append(Paragraph("✓ <b>Licensed Operation:</b> Lao government license through 2030", body_style))
    elements.append(Paragraph("✓ Flexible packaging: 2-5 kg samples to containerized shipments", body_style))

    elements.append(Spacer(1, 0.3*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph(
        f"<i>Contact us today for samples and quotations: {COMPANY_EMAIL}</i>",
        ParagraphStyle('footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)))

    add_compliance_footer(elements)

    doc.build(elements)
    print("✓ Created: 01_Brochure.pdf")

def create_technical_datasheet():
    """02_Technical_Data_Sheet.pdf - Detailed specifications"""
    doc = SimpleDocTemplate("../attachments/02_Technical_Data_Sheet.pdf", pagesize=letter)
    elements = []

    add_header(elements, "Technical Data Sheet - High-Purity Quartz")

    elements.append(Paragraph("<b>Chemical Composition (ICP-MS Analysis)</b>", heading_style))

    composition_data = [
        ['Element', 'Grade A Spec', 'Grade B Spec', 'Typical Value'],
        ['SiO₂', '99.5-99.89%', '99.0-99.49%', '99.6% (Grade A)'],
        ['Fe₂O₃ (Iron)', '0.24-0.30 ppm', '< 500 ppm', '0.27 ppm'],
        ['B (Boron)', '34.6 ppb', '< 100 ppb', '34.6 ppb'],
        ['Al₂O₃', '< 500 ppm', '< 1000 ppm', '350 ppm'],
        ['TiO₂', '< 200 ppm', '< 500 ppm', '180 ppm'],
        ['Na₂O', '< 50 ppm', '< 200 ppm', '40 ppm'],
        ['K₂O', '< 50 ppm', '< 200 ppm', '35 ppm'],
        ['CaO', '< 100 ppm', '< 300 ppm', '80 ppm'],
        ['MgO', '< 50 ppm', '< 150 ppm', '42 ppm'],
        ['P₂O₅', '< 50 ppm', '< 100 ppm', '38 ppm']
    ]

    table = Table(composition_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    elements.append(table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Physical Properties</b>", heading_style))

    physical_data = [
        ['Property', 'Value'],
        ['Particle Size Range', '10-500 μm (customizable)'],
        ['Bulk Density', '1.4-1.6 g/cm³'],
        ['Melting Point', '1710°C'],
        ['Mohs Hardness', '7'],
        ['Color', 'White to translucent'],
        ['Crystalline Structure', 'Hexagonal']
    ]

    table2 = Table(physical_data, colWidths=[3*inch, 3.5*inch])
    table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#283593')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(table2)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Quality Control</b>", heading_style))
    elements.append(Paragraph("• ICP-MS analysis for all batches", body_style))
    elements.append(Paragraph("• XRF verification", body_style))
    elements.append(Paragraph("• Particle size distribution analysis", body_style))
    elements.append(Paragraph("• Certificate of Analysis (COA) provided with each shipment", body_style))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Packaging</b>", heading_style))
    elements.append(Paragraph("• Sample: 2-5 kg in sealed bags", body_style))
    elements.append(Paragraph("• Bulk: 25 kg bags or 1000 kg super sacks", body_style))
    elements.append(Paragraph("• Custom packaging available upon request", body_style))

    doc.build(elements)
    print("✓ Created: 02_Technical_Data_Sheet.pdf")

def create_detailed_brochure():
    """04_Detailed_Brochure.pdf - Extended technical information"""
    doc = SimpleDocTemplate("../attachments/04_Detailed_Brochure.pdf", pagesize=letter)
    elements = []

    add_header(elements, "Detailed Product Information & ICP-MS Data")

    elements.append(Paragraph("<b>Quality Assurance & Testing</b>", heading_style))
    elements.append(Paragraph(
        """Our high-purity quartz undergoes rigorous testing at every stage of production.
        We employ state-of-the-art ICP-MS (Inductively Coupled Plasma Mass Spectrometry)
        to ensure trace element concentrations meet or exceed industry standards. Each batch
        is tested for over 40 elements to guarantee consistent purity.""", body_style))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Applications by Industry</b>", heading_style))

    applications = [
        ['<b>Semiconductor Industry</b>', 'Ultra-pure quartz crucibles, wafer processing, etching chemicals'],
        ['<b>Solar Energy</b>', 'Photovoltaic cell production, quartz tubes for ingot growing'],
        ['<b>Optical Fiber</b>', 'Preform production, high-transparency fiber optics'],
        ['<b>Specialty Glass</b>', 'Low-expansion glass, UV-transmitting optics'],
        ['<b>Research & Development</b>', 'Laboratory equipment, custom formulations']
    ]

    app_table = Table(applications, colWidths=[2.5*inch, 4*inch])
    app_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
    ]))
    elements.append(app_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Boron & Critical Impurities Control</b>", heading_style))
    elements.append(Paragraph(
        """Boron content is critical for semiconductor applications. Our specialized purification
        process reduces boron to < 0.3 ppm, well below industry requirements. We also control
        alkali metals (Na, K, Li) and transition metals (Fe, Ti, Cr) to ultra-trace levels.""",
        body_style))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Particle Size Options</b>", heading_style))

    sizes_data = [
        ['Grade', 'Particle Size', 'Best For'],
        ['Fine Powder', '< 45 μm', 'Coatings, ceramics'],
        ['Standard Sand', '100-500 μm', 'Glass production'],
        ['Coarse Sand', '500-1000 μm', 'Crucibles, refractories'],
        ['Granules', '1-5 mm', 'Filtration, specialty applications'],
        ['Custom', 'Per specification', 'Your specific needs']
    ]

    sizes_table = Table(sizes_data, colWidths=[1.8*inch, 2*inch, 2.7*inch])
    sizes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
    ]))
    elements.append(sizes_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Request Your Free Sample Today</b>", heading_style))
    elements.append(Paragraph(
        """We offer complimentary 2-5 kg samples for qualified buyers. Contact us with your
        specifications, and we'll prepare a sample batch with full COA documentation.""",
        body_style))

    doc.build(elements)
    print("✓ Created: 04_Detailed_Brochure.pdf")

def create_sample_request_form():
    """Sample_Request_Form.pdf - Form for customers"""
    doc = SimpleDocTemplate("../attachments/Sample_Request_Form.pdf", pagesize=letter)
    elements = []

    add_header(elements, "Sample Request Form")

    elements.append(Paragraph(
        "Please complete this form to request a 2-5 kg complimentary sample of our high-purity quartz products.",
        body_style))
    elements.append(Spacer(1, 0.3*inch))

    # Company information section
    elements.append(Paragraph("<b>Company Information</b>", heading_style))
    form_data = [
        ['Company Name:', '_' * 80],
        ['Industry:', '_' * 80],
        ['Contact Person:', '_' * 80],
        ['Title/Position:', '_' * 80],
        ['Email:', '_' * 80],
        ['Phone:', '_' * 80],
        ['Shipping Address:', '_' * 80],
        ['', '_' * 80],
    ]

    for row in form_data:
        elements.append(Paragraph(f"{row[0]} {row[1]}", body_style))
        elements.append(Spacer(1, 0.1*inch))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Product Specifications</b>", heading_style))

    spec_data = [
        ['Required Purity (SiO₂):', '☐ 99.9%   ☐ 99.95%   ☐ 99.99%   ☐ Other: _____________'],
        ['Particle Size:', '☐ < 45 μm   ☐ 100-500 μm   ☐ Custom: _____________'],
        ['Sample Quantity:', '☐ 2 kg   ☐ 5 kg   ☐ Other: _____________'],
        ['Intended Application:', '_' * 70],
        ['', '_' * 70],
        ['Boron Content:', '☐ < 0.5 ppm   ☐ < 1 ppm   ☐ Not critical'],
        ['Expected Annual Volume:', '_' * 70]
    ]

    for row in spec_data:
        elements.append(Paragraph(f"{row[0]} {row[1]}", body_style))
        elements.append(Spacer(1, 0.1*inch))

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Additional Requirements</b>", heading_style))
    elements.append(Paragraph('_' * 100, body_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph('_' * 100, body_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph('_' * 100, body_style))

    elements.append(Spacer(1, 0.4*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph(
        f"<i>Submit this form to: {COMPANY_EMAIL} | We'll ship your sample within 5-7 business days</i>",
        ParagraphStyle('footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9)))

    doc.build(elements)
    print("✓ Created: Sample_Request_Form.pdf")

def create_quotation_template():
    """03_Quotation.pdf - Pricing template"""
    doc = SimpleDocTemplate("../attachments/03_Quotation.pdf", pagesize=letter)
    elements = []

    add_header(elements, "Price Quotation")

    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", body_style))
    elements.append(Paragraph("<b>Valid Until:</b> [30 days from date]", body_style))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>To:</b>", heading_style))
    elements.append(Paragraph("[Customer Company Name]", body_style))
    elements.append(Paragraph("[Contact Person]", body_style))
    elements.append(Paragraph("[Email]", body_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>Quotation Details</b>", heading_style))

    quote_data = [
        ['Item', 'Specification', 'Quantity', 'Unit Price', 'Total'],
        ['High-Purity Quartz Sand', 'SiO₂ > 99.99%\n100-500 μm', '1000 kg', 'USD [X]/kg', 'USD [XXX]'],
        ['', '', '', '', ''],
        ['', '', '', '<b>Subtotal:</b>', 'USD [XXX]'],
        ['', '', '', '<b>Shipping (FOB/CIF):</b>', 'USD [XXX]'],
        ['', '', '', '<b>Total:</b>', '<b>USD [XXX]</b>']
    ]

    quote_table = Table(quote_data, colWidths=[1.8*inch, 2*inch, 1.2*inch, 1.2*inch, 1.3*inch])
    quote_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, 2), 1, colors.grey),
        ('BACKGROUND', (0, 1), (-1, 2), colors.beige),
        ('LINEABOVE', (3, 3), (-1, 3), 1, colors.grey),
        ('LINEABOVE', (3, 5), (-1, 5), 2, colors.black),
        ('FONTNAME', (3, 5), (-1, 5), 'Helvetica-Bold')
    ]))
    elements.append(quote_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Terms & Conditions</b>", heading_style))
    elements.append(Paragraph("• <b>Payment Terms:</b> 30% deposit, 70% before shipment (T/T)", body_style))
    elements.append(Paragraph("• <b>Lead Time:</b> 15-20 days after deposit", body_style))
    elements.append(Paragraph("• <b>Packaging:</b> 25 kg bags or 1000 kg super sacks", body_style))
    elements.append(Paragraph("• <b>Shipping:</b> FOB Vientiane / CIF [Your Port]", body_style))
    elements.append(Paragraph("• <b>Documentation:</b> COA, Commercial Invoice, Packing List, B/L", body_style))
    elements.append(Paragraph("• <b>Validity:</b> Prices valid for 30 days from quotation date", body_style))

    elements.append(Spacer(1, 0.4*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph("<b>For Orders or Questions:</b>",
                             ParagraphStyle('contact', parent=styles['Normal'], fontSize=10)))
    elements.append(Paragraph(f"{COMPANY_EMAIL} | {COMPANY_PHONE}",
                             ParagraphStyle('contact', parent=styles['Normal'], fontSize=10)))

    doc.build(elements)
    print("✓ Created: 03_Quotation.pdf")

def create_contract_template():
    """Contract_Template.pdf - Sales contract"""
    doc = SimpleDocTemplate("../attachments/Contract_Template.pdf", pagesize=letter)
    elements = []

    add_header(elements, "Sales Contract")

    elements.append(Paragraph(f"<b>Contract No:</b> QTZ-{datetime.now().strftime('%Y%m%d')}-[XXX]", body_style))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", body_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>Seller:</b>", heading_style))
    elements.append(Paragraph(COMPANY_NAME, body_style))
    elements.append(Paragraph(f"Address: {COMPANY_ADDRESS}", body_style))
    elements.append(Paragraph(f"Email: {COMPANY_EMAIL}", body_style))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>Buyer:</b>", heading_style))
    elements.append(Paragraph("[Customer Company Name]", body_style))
    elements.append(Paragraph("[Customer Address]", body_style))
    elements.append(Paragraph("[Customer Contact]", body_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>Article 1: Product Specifications</b>", heading_style))

    contract_data = [
        ['Product', 'Specifications', 'Quantity', 'Unit Price', 'Total Amount'],
        ['High-Purity Quartz', 'SiO₂ > 99.99%\nParticle: 100-500 μm', '[XXX] kg', 'USD [X]/kg', 'USD [XXXX]']
    ]

    contract_table = Table(contract_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1*inch, 1*inch])
    contract_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
    ]))
    elements.append(contract_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Article 2: Payment Terms</b>", heading_style))
    elements.append(Paragraph("1. Deposit: 30% of total amount upon contract signing", body_style))
    elements.append(Paragraph("2. Balance: 70% before shipment", body_style))
    elements.append(Paragraph("3. Payment Method: Telegraphic Transfer (T/T)", body_style))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Article 3: Delivery Terms</b>", heading_style))
    elements.append(Paragraph("1. Delivery Time: 15-20 days after deposit receipt", body_style))
    elements.append(Paragraph("2. Shipping Terms: FOB Vientiane / CIF [Destination Port]", body_style))
    elements.append(Paragraph("3. Packaging: 25 kg bags in pallets or 1000 kg super sacks", body_style))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Article 4: Quality Guarantee</b>", heading_style))
    elements.append(Paragraph("1. Certificate of Analysis (COA) provided with each shipment", body_style))
    elements.append(Paragraph("2. ICP-MS test results for all specified elements", body_style))
    elements.append(Paragraph("3. Product must meet specifications stated in Article 1", body_style))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Article 5: Force Majeure</b>", heading_style))
    elements.append(Paragraph(
        "Neither party shall be liable for failure to perform due to circumstances beyond reasonable control.",
        body_style))

    elements.append(Spacer(1, 0.4*inch))
    elements.append(Paragraph("<b>Signatures:</b>", heading_style))

    signature_data = [
        ['<b>Seller:</b>', '<b>Buyer:</b>'],
        ['', ''],
        ['_' * 30, '_' * 30],
        ['Name: Jenny Lalita', 'Name: _______________'],
        ['Title: [Your Title]', 'Title: _______________'],
        ['Date: _______________', 'Date: _______________']
    ]

    sig_table = Table(signature_data, colWidths=[3.3*inch, 3.3*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0)
    ]))
    elements.append(sig_table)

    doc.build(elements)
    print("✓ Created: Contract_Template.pdf")

def create_coa():
    """COA.pdf - Certificate of Analysis"""
    doc = SimpleDocTemplate("../attachments/COA.pdf", pagesize=letter)
    elements = []

    add_header(elements, "Certificate of Analysis (COA)")

    elements.append(Paragraph(f"<b>COA Number:</b> COA-{datetime.now().strftime('%Y%m%d')}-[XXX]", body_style))
    elements.append(Paragraph(f"<b>Issue Date:</b> {datetime.now().strftime('%B %d, %Y')}", body_style))
    elements.append(Paragraph("<b>Product:</b> High-Purity Quartz Sand", body_style))
    elements.append(Paragraph("<b>Batch Number:</b> [BATCH-XXXX]", body_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>Chemical Analysis (ICP-MS)</b>", heading_style))

    coa_data = [
        ['Element', 'Specification', 'Test Result', 'Unit', 'Status'],
        ['SiO₂', '≥ 99.99%', '99.995%', 'wt%', '✓ Pass'],
        ['Al₂O₃', '< 50 ppm', '28 ppm', 'ppm', '✓ Pass'],
        ['Fe₂O₃', '< 10 ppm', '4.2 ppm', 'ppm', '✓ Pass'],
        ['Na₂O', '< 5 ppm', '1.8 ppm', 'ppm', '✓ Pass'],
        ['K₂O', '< 5 ppm', '1.5 ppm', 'ppm', '✓ Pass'],
        ['CaO', '< 5 ppm', '2.1 ppm', 'ppm', '✓ Pass'],
        ['TiO₂', '< 5 ppm', '1.9 ppm', 'ppm', '✓ Pass'],
        ['B', '< 0.5 ppm', '0.28 ppm', 'ppm', '✓ Pass'],
        ['P', '< 1 ppm', '0.42 ppm', 'ppm', '✓ Pass'],
        ['Li', '< 0.5 ppm', '0.18 ppm', 'ppm', '✓ Pass']
    ]

    coa_table = Table(coa_data, colWidths=[1.3*inch, 1.3*inch, 1.3*inch, 0.8*inch, 1*inch])
    coa_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (4, 1), (4, -1), colors.green)
    ]))
    elements.append(coa_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Physical Properties</b>", heading_style))

    physical_coa = [
        ['Property', 'Specification', 'Test Result', 'Status'],
        ['Particle Size', '100-500 μm', '120-480 μm', '✓ Pass'],
        ['Bulk Density', '1.4-1.6 g/cm³', '1.52 g/cm³', '✓ Pass'],
        ['Moisture Content', '< 0.1%', '0.05%', '✓ Pass'],
        ['Color', 'White/Translucent', 'White', '✓ Pass']
    ]

    phys_table = Table(physical_coa, colWidths=[2*inch, 1.8*inch, 1.5*inch, 1.2*inch])
    phys_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#283593')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (3, 1), (3, -1), colors.green)
    ]))
    elements.append(phys_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Testing Laboratory:</b> [Certified Lab Name]", body_style))
    elements.append(Paragraph("<b>Test Method:</b> ICP-MS, XRF, Laser Diffraction", body_style))
    elements.append(Paragraph("<b>Test Date:</b> " + datetime.now().strftime('%Y-%m-%d'), body_style))

    elements.append(Spacer(1, 0.4*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph("<b>Approved by:</b>", body_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("_" * 40, body_style))
    elements.append(Paragraph("Quality Control Manager", body_style))
    elements.append(Paragraph(datetime.now().strftime('%B %d, %Y'), body_style))

    doc.build(elements)
    print("✓ Created: COA.pdf")

def create_shipping_docs():
    """Shipping_Docs.pdf - Shipping documentation"""
    doc = SimpleDocTemplate("../attachments/Shipping_Docs.pdf", pagesize=letter)
    elements = []

    add_header(elements, "Shipping Documentation")

    elements.append(Paragraph(f"<b>Shipment No:</b> SHIP-{datetime.now().strftime('%Y%m%d')}-[XXX]", body_style))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", body_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>Shipper (Seller):</b>", heading_style))
    elements.append(Paragraph(COMPANY_NAME, body_style))
    elements.append(Paragraph(COMPANY_ADDRESS, body_style))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>Consignee (Buyer):</b>", heading_style))
    elements.append(Paragraph("[Customer Company Name]", body_style))
    elements.append(Paragraph("[Customer Address]", body_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>Packing List</b>", heading_style))

    packing_data = [
        ['Box/Pallet No.', 'Description', 'Quantity', 'Net Weight', 'Gross Weight'],
        ['1', 'High-Purity Quartz Sand', '[XX] bags', '[XXX] kg', '[XXX] kg'],
        ['2', 'High-Purity Quartz Sand', '[XX] bags', '[XXX] kg', '[XXX] kg'],
        ['', '', '<b>Total:</b>', '<b>[XXX] kg</b>', '<b>[XXX] kg</b>']
    ]

    packing_table = Table(packing_data, colWidths=[1.3*inch, 2.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    packing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('LINEABOVE', (2, -1), (-1, -1), 2, colors.black)
    ]))
    elements.append(packing_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Shipping Information</b>", heading_style))
    elements.append(Paragraph("<b>Port of Loading:</b> [Vientiane/Bangkok]", body_style))
    elements.append(Paragraph("<b>Port of Discharge:</b> [Customer Port]", body_style))
    elements.append(Paragraph("<b>Shipping Terms:</b> FOB / CIF", body_style))
    elements.append(Paragraph("<b>Vessel/Flight:</b> [TBD]", body_style))
    elements.append(Paragraph("<b>Container No:</b> [TBD]", body_style))
    elements.append(Paragraph("<b>B/L Number:</b> [TBD]", body_style))

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Documents Included:</b>", heading_style))
    elements.append(Paragraph("☐ Commercial Invoice", body_style))
    elements.append(Paragraph("☐ Packing List", body_style))
    elements.append(Paragraph("☐ Certificate of Analysis (COA)", body_style))
    elements.append(Paragraph("☐ Bill of Lading (B/L)", body_style))
    elements.append(Paragraph("☐ Certificate of Origin", body_style))
    elements.append(Paragraph("☐ Insurance Certificate (if CIF)", body_style))

    elements.append(Spacer(1, 0.4*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph("<b>Prepared by:</b> Shipping Department",
                             ParagraphStyle('footer', parent=styles['Normal'], fontSize=10)))
    elements.append(Paragraph(f"Contact: {COMPANY_EMAIL}",
                             ParagraphStyle('footer', parent=styles['Normal'], fontSize=10)))

    doc.build(elements)
    print("✓ Created: Shipping_Docs.pdf")

def create_satisfaction_survey():
    """Customer_Satisfaction_Survey.pdf - Post-delivery feedback form"""
    doc = SimpleDocTemplate("../attachments/Customer_Satisfaction_Survey.pdf", pagesize=letter)
    elements = []

    add_header(elements, "Customer Satisfaction Survey")

    elements.append(Paragraph(
        "Thank you for choosing Lorh La Seng for your high-purity quartz needs! Your feedback helps us improve our products and services.",
        body_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>Order Information</b>", heading_style))
    survey_data = [
        ['Order Date:', '_' * 60],
        ['Product Grade:', '☐ Grade A   ☐ Grade B   ☐ Grade C'],
        ['Quantity Received:', '_' * 60],
    ]
    for row in survey_data:
        elements.append(Paragraph(f"{row[0]} {row[1]}", body_style))
        elements.append(Spacer(1, 0.1*inch))

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Product Quality</b>", heading_style))

    quality_data = [
        ['1. Did the product meet specifications?', '☐ Yes   ☐ No   ☐ Exceeded'],
        ['2. Purity level satisfaction:', '☐ Very Satisfied   ☐ Satisfied   ☐ Needs Improvement'],
        ['3. Particle size consistency:', '☐ Excellent   ☐ Good   ☐ Fair   ☐ Poor'],
        ['4. Packaging condition:', '☐ Excellent   ☐ Good   ☐ Damaged'],
    ]
    for row in quality_data:
        elements.append(Paragraph(f"<b>{row[0]}</b>", body_style))
        elements.append(Paragraph(row[1], body_style))
        elements.append(Spacer(1, 0.15*inch))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Service Experience</b>", heading_style))

    service_data = [
        ['5. Communication & responsiveness:', '☐ Excellent   ☐ Good   ☐ Fair   ☐ Poor'],
        ['6. Delivery time:', '☐ On Time   ☐ Delayed   Days late: _____'],
        ['7. Documentation (COA, etc.):', '☐ Complete   ☐ Incomplete   ☐ Missing'],
    ]
    for row in service_data:
        elements.append(Paragraph(f"<b>{row[0]}</b>", body_style))
        elements.append(Paragraph(row[1], body_style))
        elements.append(Spacer(1, 0.15*inch))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Future Orders</b>", heading_style))
    elements.append(Paragraph("<b>8. Would you order from us again?</b>", body_style))
    elements.append(Paragraph("☐ Definitely   ☐ Probably   ☐ Maybe   ☐ No", body_style))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>9. Estimated next order quantity:</b> _" * 40, body_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>10. Additional Comments / Suggestions:</b>", body_style))
    elements.append(Paragraph('_' * 100, body_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph('_' * 100, body_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph('_' * 100, body_style))

    elements.append(Spacer(1, 0.4*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph(
        f"<i>Please return this survey to: {COMPANY_EMAIL} | Thank you!</i>",
        ParagraphStyle('footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)))

    add_compliance_footer(elements)
    doc.build(elements)
    print("✓ Created: Customer_Satisfaction_Survey.pdf")


def create_vip_program():
    """VIP_Discount_Program.pdf - Loyalty benefits for repeat customers"""
    doc = SimpleDocTemplate("../attachments/VIP_Discount_Program.pdf", pagesize=letter)
    elements = []

    add_header(elements, "VIP Customer Discount Program")

    elements.append(Paragraph(
        """Welcome to the Lorh La Seng VIP Program! As a valued repeat customer, you qualify for
        exclusive benefits and priority service.""", body_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>VIP Tier Benefits</b>", heading_style))

    tiers_data = [
        ['Tier', 'Annual Volume', 'Discount', 'Benefits'],
        ['🥉 Bronze', '50-200 tons', '3%', 'Priority support, quarterly reviews'],
        ['🥈 Silver', '200-500 tons', '5%', 'Bronze + Dedicated account manager'],
        ['🥇 Gold', '500-1000 tons', '8%', 'Silver + Custom payment terms'],
        ['💎 Platinum', '1000+ tons', '12%', 'Gold + First access to new grades']
    ]

    tiers_table = Table(tiers_data, colWidths=[1.2*inch, 1.6*inch, 1*inch, 2.7*inch])
    tiers_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
    ]))
    elements.append(tiers_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>All VIP Members Receive:</b>", heading_style))
    elements.append(Paragraph("✓ Volume-based pricing discounts", body_style))
    elements.append(Paragraph("✓ Flexible payment terms (30-90 days)", body_style))
    elements.append(Paragraph("✓ Priority production scheduling", body_style))
    elements.append(Paragraph("✓ Free sample testing for new grades", body_style))
    elements.append(Paragraph("✓ Quarterly business reviews", body_style))
    elements.append(Paragraph("✓ Dedicated account manager (Silver+)", body_style))
    elements.append(Paragraph("✓ Custom packaging options", body_style))

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>How to Join</b>", heading_style))
    elements.append(Paragraph(
        "Contact your account manager or email us at " + COMPANY_EMAIL + " to discuss VIP enrollment. "
        "Benefits apply immediately upon approval.", body_style))

    elements.append(Spacer(1, 0.3*inch))
    add_compliance_footer(elements)
    doc.build(elements)
    print("✓ Created: VIP_Discount_Program.pdf")


def create_bulk_benefits():
    """Bulk_Order_Benefits.pdf - Advantages of larger orders"""
    doc = SimpleDocTemplate("../attachments/Bulk_Order_Benefits.pdf", pagesize=letter)
    elements = []

    add_header(elements, "Bulk Order Benefits")

    elements.append(Paragraph(
        "<b>Save More with Larger Orders!</b>", heading_style))
    elements.append(Paragraph(
        """At Lorh La Seng, we reward customers who order in volume with significant cost savings,
        priority service, and flexible logistics.""", body_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>Volume Pricing</b>", heading_style))

    pricing_data = [
        ['Order Size', 'Discount', 'Savings Example (on $10,000 order)'],
        ['< 50 tons', '0%', 'Base price: $10,000'],
        ['50-100 tons', '5%', 'Save: $500'],
        ['100-200 tons', '8%', 'Save: $800'],
        ['200-500 tons', '12%', 'Save: $1,200'],
        ['500+ tons', '15%', 'Save: $1,500+'],
        ['Container load', 'Custom', 'Contact for quote']
    ]

    pricing_table = Table(pricing_data, colWidths=[2*inch, 1.5*inch, 3*inch])
    pricing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
    ]))
    elements.append(pricing_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Additional Bulk Benefits:</b>", heading_style))

    benefits_data = [
        ['📦 Flexible Packaging', 'Super sacks, containers, or custom packaging at no extra cost'],
        ['🚢 Logistics Support', 'We arrange shipping, customs clearance, and documentation'],
        ['📅 Production Priority', 'Your large orders get priority scheduling'],
        ['💰 Payment Terms', '30-90 day terms available for qualified buyers'],
        ['🔬 Free Testing', 'Complimentary ICP-MS testing for orders over 100 tons'],
        ['📊 Market Insights', 'Quarterly reports on industry trends and pricing']
    ]

    for benefit in benefits_data:
        elements.append(Paragraph(f"<b>{benefit[0]}</b>", body_style))
        elements.append(Paragraph(f"  {benefit[1]}", body_style))
        elements.append(Spacer(1, 0.1*inch))

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Ready to Save?</b>", heading_style))
    elements.append(Paragraph(
        f"Contact us today at {COMPANY_EMAIL} or call {COMPANY_PHONE} to discuss bulk pricing for your next order. "
        "Our team will prepare a custom quote within 24 hours.", body_style))

    elements.append(Spacer(1, 0.3*inch))
    add_compliance_footer(elements)
    doc.build(elements)
    print("✓ Created: Bulk_Order_Benefits.pdf")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Generating PDF Templates for Quartz Email System")
    print("="*60 + "\n")

    create_brochure()
    create_technical_datasheet()
    create_detailed_brochure()
    create_sample_request_form()
    create_quotation_template()
    create_contract_template()
    create_coa()
    create_shipping_docs()
    create_satisfaction_survey()
    create_vip_program()
    create_bulk_benefits()

    print("\n" + "="*60)
    print("  ✓ All PDF templates created successfully!")
    print("  Location: /attachments/")
    print("  Next: Customize the templates with your actual data")
    print("="*60 + "\n")
