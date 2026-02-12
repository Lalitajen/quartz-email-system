#!/usr/bin/env python3
"""
Test that different email content triggers different pipeline stages
"""

import os
import sys
sys.path.append('scripts')

from dotenv import load_dotenv
load_dotenv('config/.env')

from anthropic import Anthropic

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Test emails for different stages
test_emails = [
    {
        "stage": 1,
        "content": "Hi, I'm interested in learning more about your company and products. Can you send me some information?"
    },
    {
        "stage": 2,
        "content": "Can you send me the technical specifications and data sheets for your quartz products?"
    },
    {
        "stage": 3,
        "content": "I need detailed information about the boron content and ICP-MS analysis. What's the purity level?"
    },
    {
        "stage": 4,
        "content": "We'd like to request a 2-5kg sample for laboratory testing. Can you send a sample request form?"
    },
    {
        "stage": 5,
        "content": "What's your pricing? Can you send a quotation with FOB and CIF costs?"
    },
    {
        "stage": 6,
        "content": "We're ready to place an order. Please send the contract and payment terms."
    },
    {
        "stage": 7,
        "content": "When will our shipment arrive? Do you have the COA and shipping documents ready?"
    },
    {
        "stage": 8,
        "content": "We received the product. Can you send a satisfaction survey? We'd like to provide feedback."
    },
    {
        "stage": 9,
        "content": "We want to place another bulk order. Do you have volume discounts for container loads?"
    }
]

# Expected attachments per stage
EXPECTED_ATTACHMENTS = {
    1: ["01_Brochure.pdf"],
    2: ["01_Brochure.pdf", "02_Technical_Data_Sheet.pdf"],
    3: ["02_Technical_Data_Sheet.pdf", "04_Detailed_Brochure.pdf"],
    4: ["02_Technical_Data_Sheet.pdf", "Sample_Request_Form.pdf"],
    5: ["03_Quotation.pdf"],
    6: ["Contract_Template.pdf", "03_Quotation.pdf"],
    7: ["COA.pdf", "Shipping_Docs.pdf"],
    8: ["Customer_Satisfaction_Survey.pdf"],
    9: ["VIP_Discount_Program.pdf", "Bulk_Order_Benefits.pdf"]
}

def analyze_email(email_body):
    """Analyze email to detect stage"""
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Analyze this customer email and determine which pipeline stage they're at (1-9).

Email content:
{email_body}

Pipeline stages:
1. Prospecting - General interest
2. Initial Contact - Want specs/details
3. Qualification - Technical questions (ICP-MS, purity, boron, etc.)
4. Sample & Testing - Want samples
5. Negotiation - Pricing questions
6. Contract - Ready to order
7. Fulfillment - Delivery/shipping
8. Follow-Up - Feedback/satisfaction
9. Repeat Customer - Want more orders

Respond with ONLY the stage number (1-9)."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}]
    )

    response = message.content[0].text.strip()
    try:
        return int(response)
    except:
        return 1

print("\n" + "="*70)
print("  🧪 TESTING PIPELINE STAGE DETECTION")
print("="*70 + "\n")

correct = 0
total = len(test_emails)

for test in test_emails:
    expected_stage = test['stage']
    email_content = test['content']

    print(f"Test Email (Expected Stage {expected_stage}):")
    print(f"  \"{email_content[:60]}...\"")
    print(f"  Analyzing...", end=" ")

    detected_stage = analyze_email(email_content)

    if detected_stage == expected_stage:
        print(f"✅ Detected: Stage {detected_stage}")
        print(f"  PDFs: {', '.join(EXPECTED_ATTACHMENTS[detected_stage])}")
        correct += 1
    else:
        print(f"❌ Detected: Stage {detected_stage} (Expected: {expected_stage})")
        print(f"  PDFs: {', '.join(EXPECTED_ATTACHMENTS[detected_stage])}")

    print()

print("="*70)
print(f"Results: {correct}/{total} correct ({correct/total*100:.1f}%)")
print("="*70 + "\n")

if correct == total:
    print("✅ All stages detected correctly!")
    print("   PDFs will change based on customer's message")
else:
    print("⚠️  Some stages not detected correctly")
    print("   AI might need more context or keywords")
