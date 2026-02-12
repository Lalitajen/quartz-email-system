#!/usr/bin/env python3
"""Quick test of email generation to see exact error"""

import os
from dotenv import load_dotenv
load_dotenv('config/.env')

from anthropic import Anthropic

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

print("🧪 Testing AI Email Generation...")
print(f"API Key: {ANTHROPIC_API_KEY[:20]}..." if ANTHROPIC_API_KEY else "❌ No API key")

try:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    print("\n📧 Generating test email...")
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": "Write a 2-sentence B2B email introducing high-purity quartz."
        }]
    )

    result = message.content[0].text
    print("✅ SUCCESS! Email generated:")
    print("-" * 60)
    print(result)
    print("-" * 60)

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")

    if "credit balance is too low" in str(e):
        print("\n💡 SOLUTION:")
        print("   Add credits at: https://console.anthropic.com/settings/billing")
        print("   OR: https://platform.claude.com/settings/billing")
    elif "api_key" in str(e).lower():
        print("\n💡 SOLUTION:")
        print("   Check ANTHROPIC_API_KEY in config/.env")
    else:
        print("\n💡 Check the error message above for details")
