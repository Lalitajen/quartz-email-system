#!/usr/bin/env python3
"""
Test script for SmartIntentDetectionEngine.
Tests multi-intent detection, sentiment analysis, and confidence scoring.
"""

import os
import sys

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

from ai_engines import SmartIntentDetectionEngine

# Test cases
TEST_EMAILS = [
    {
        "name": "Multi-Intent (Sample + Pricing + Urgency)",
        "subject": "Re: Quartz Sample Inquiry",
        "body": """Hi Jenny,

Thanks for the info! We're looking to test your HPQ-99.99 material in our
new semiconductor fab. Can you rush a 5kg sample by next week? Also, what's
your pricing for 10-ton monthly orders? Our purchasing manager wants to
evaluate 2-3 suppliers before Q3.

Need this ASAP as our current supplier just raised prices 15%.

Best,
Tom Chen
Sr. Process Engineer""",
        "expected_primary": "sample_request",
        "expected_confidence": 0.9,
        "expected_urgency": "high",
        "expected_buying_signals": True,
    },
    {
        "name": "Simple Info Request",
        "subject": "Inquiry",
        "body": "Hi, we're interested in learning more about your high-purity quartz. Can you send a brochure?",
        "expected_primary": "info_request",
        "expected_confidence": 0.9,
        "expected_urgency": "low",
        "expected_buying_signals": False,
    },
    {
        "name": "Clear Decline",
        "subject": "Re: Quote",
        "body": "Thanks but we've decided to go with another supplier. Please remove us from your mailing list.",
        "expected_primary": "declined",
        "expected_confidence": 0.95,
        "expected_urgency": "low",
        "expected_buying_signals": False,
    },
    {
        "name": "Technical Request",
        "subject": "Technical Specs",
        "body": "Can you provide the technical specs and ICP analysis report for your HPQ-99.99 grade? We need SiO2 purity data.",
        "expected_primary": "technical_info_request",
        "expected_confidence": 0.85,
        "expected_urgency": "medium",
        "expected_buying_signals": True,
    },
]


def test_intent_detection():
    """Run all test cases."""
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found in config/.env")
        print("Please add your Anthropic API key to proceed with testing.")
        return

    print("=" * 70)
    print("  SmartIntentDetectionEngine Test Suite")
    print("=" * 70)
    print()

    engine = SmartIntentDetectionEngine(api_key)

    if not engine.client:
        print("❌ ERROR: Failed to initialize Anthropic client")
        return

    results = []
    for i, test in enumerate(TEST_EMAILS, 1):
        print(f"Test {i}/{len(TEST_EMAILS)}: {test['name']}")
        print("-" * 70)
        print(f"Subject: {test['subject']}")
        print(f"Body: {test['body'][:100]}...")
        print()

        # Run analysis
        result = engine.analyze_email_intent(
            email_body=test['body'],
            subject=test['subject'],
            current_stage=1
        )

        # Display results
        print(f"✓ Primary Intent: {result['primary_intent']}")
        print(f"✓ Secondary Intents: {result.get('secondary_intents', [])}")
        print(f"✓ Urgency: {result['urgency_level']}")
        print(f"✓ Sentiment: {result['sentiment']}")
        print(f"✓ Confidence: {result['confidence_score']:.2f}")
        print(f"✓ Recommended Stage: {result['recommended_stage']}")
        print(f"✓ Buying Signals: {result.get('buying_signals', [])}")
        print(f"✓ Objections: {result.get('objections', [])}")
        print(f"✓ Reasoning: {result.get('reasoning', 'N/A')}")
        print()

        # Validate expectations
        passed = True
        if result['primary_intent'] != test['expected_primary']:
            print(f"⚠️  Expected intent '{test['expected_primary']}' but got '{result['primary_intent']}'")
            passed = False

        if result['confidence_score'] < test['expected_confidence']:
            print(f"⚠️  Confidence {result['confidence_score']:.2f} below expected {test['expected_confidence']:.2f}")
            passed = False

        if result['urgency_level'] != test['expected_urgency']:
            print(f"⚠️  Expected urgency '{test['expected_urgency']}' but got '{result['urgency_level']}'")
            passed = False

        if test['expected_buying_signals']:
            if len(result.get('buying_signals', [])) == 0:
                print(f"⚠️  Expected buying signals but found none")
                passed = False

        if passed:
            print("✅ PASSED")
        else:
            print("❌ FAILED")

        results.append(passed)
        print()
        print("=" * 70)
        print()

    # Summary
    passed_count = sum(results)
    total_count = len(results)
    accuracy = (passed_count / total_count * 100) if total_count > 0 else 0

    print()
    print("SUMMARY")
    print("=" * 70)
    print(f"Tests Passed: {passed_count}/{total_count} ({accuracy:.1f}%)")
    print(f"Goal: 95%+ accuracy")

    if accuracy >= 95:
        print("✅ SUCCESS: AI accuracy meets 95%+ goal!")
    elif accuracy >= 80:
        print("⚠️  GOOD: AI accuracy is above 80%, but below 95% goal")
    else:
        print("❌ NEEDS IMPROVEMENT: AI accuracy below 80%")

    print()


if __name__ == "__main__":
    test_intent_detection()
