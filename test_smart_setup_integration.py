#!/usr/bin/env python3
"""
Integration test for Smart Setup Assistant
Tests that all components are properly integrated and working.
"""

import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        from routes.smart_setup import smart_setup_bp, analyze_setup_status
        print("✅ smart_setup_bp imported successfully")

        from app_core import create_user_sheet_template, get_sheets, get_gmail_service_for_user
        print("✅ app_core helper functions imported successfully")

        from models import User, init_db
        print("✅ User model imported successfully")

        from flask import Flask
        print("✅ Flask imported successfully")

        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_blueprint_registration():
    """Test that smart_setup_bp is registered in routes.__init__."""
    print("\nTesting blueprint registration...")
    try:
        from routes import ALL_BLUEPRINTS

        blueprint_names = [bp.name for bp in ALL_BLUEPRINTS]

        if 'smart_setup' in blueprint_names:
            print(f"✅ smart_setup_bp is registered in ALL_BLUEPRINTS")
            print(f"   Total blueprints: {len(ALL_BLUEPRINTS)}")
            print(f"   Blueprints: {', '.join(blueprint_names)}")
            return True
        else:
            print(f"❌ smart_setup_bp NOT found in ALL_BLUEPRINTS")
            print(f"   Available: {', '.join(blueprint_names)}")
            return False
    except Exception as e:
        print(f"❌ Blueprint registration test failed: {e}")
        return False


def test_app_creation():
    """Test that the Flask app can be created with all blueprints."""
    print("\nTesting app creation...")
    try:
        from web_app import create_app

        app = create_app()

        print(f"✅ Flask app created successfully")
        print(f"   Secret key configured: {bool(app.secret_key)}")
        print(f"   Max content length: {app.config.get('MAX_CONTENT_LENGTH', 0) / (1024*1024)}MB")

        # Check that /smart-setup route exists
        with app.test_client() as client:
            # This will fail with redirect to login, but proves route exists
            response = client.get('/smart-setup', follow_redirects=False)

            if response.status_code in [200, 302]:  # 200 if logged in, 302 if redirect to login
                print(f"✅ /smart-setup route exists (status: {response.status_code})")
                return True
            else:
                print(f"❌ /smart-setup route returned unexpected status: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ App creation test failed: {e}")
        return False


def test_template_exists():
    """Test that smart_setup.html template exists and is valid."""
    print("\nTesting template...")
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'smart_setup.html')

        if not os.path.exists(template_path):
            print(f"❌ Template not found: {template_path}")
            return False

        with open(template_path, 'r') as f:
            content = f.read()

        # Check for key elements
        checks = {
            'extends base.html': '{% extends "base.html" %}' in content,
            'title block': '{% block title %}' in content,
            'progress bar': 'progress-bar' in content,
            'quick config form': '/smart-setup/quick-config' in content,
            'auto-complete button': '/smart-setup/auto-complete' in content,
            'test all button': '/smart-setup/test-all' in content,
            'credential status cards': 'setup_status.credentials' in content,
        }

        all_passed = True
        for check_name, passed in checks.items():
            if passed:
                print(f"✅ Template has {check_name}")
            else:
                print(f"❌ Template missing {check_name}")
                all_passed = False

        if all_passed:
            print(f"✅ Template is complete ({len(content)} bytes)")
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False


def test_navigation_link():
    """Test that navigation link exists in base.html."""
    print("\nTesting navigation link...")
    try:
        base_template_path = os.path.join(os.path.dirname(__file__), 'templates', 'base.html')

        with open(base_template_path, 'r') as f:
            content = f.read()

        if '/smart-setup' in content and 'Smart Setup' in content:
            print("✅ Navigation link exists in base.html")
            return True
        else:
            print("❌ Navigation link NOT found in base.html")
            return False

    except Exception as e:
        print(f"❌ Navigation link test failed: {e}")
        return False


def test_analyze_setup_status():
    """Test the analyze_setup_status function logic."""
    print("\nTesting analyze_setup_status function...")
    try:
        from routes.smart_setup import analyze_setup_status

        # Create mock user
        class MockUser:
            def __init__(self):
                self.google_sheets_id = None
                self._credentials = {}

            def has_credential(self, key):
                return key in self._credentials

        user = MockUser()

        # Test with no credentials
        status = analyze_setup_status(user)

        assert status['total_steps'] == 4, "Should have 4 total steps"
        assert status['completed_steps'] == 0, "Should have 0 completed steps initially"
        assert status['overall_completion'] == 0, "Should be 0% complete initially"
        assert status['next_action'] == 'anthropic_api_key', "Should recommend API key first"
        assert status['can_auto_complete'] == False, "Cannot auto-complete without credentials"

        print("✅ analyze_setup_status returns correct structure")
        print(f"   Total steps: {status['total_steps']}")
        print(f"   Credentials tracked: {len(status['credentials'])}")
        print(f"   Next action recommendation: {status['next_action']}")

        # Test with API key and service account
        user._credentials = {'anthropic_api_key': 'test', 'service_account': 'test'}
        status = analyze_setup_status(user)

        assert status['completed_steps'] == 2, "Should have 2 completed steps"
        assert status['overall_completion'] == 50, "Should be 50% complete"
        assert status['can_auto_complete'] == True, "Can auto-complete with API key + SA"

        print("✅ analyze_setup_status correctly calculates completion")
        print(f"   50% completion detected: {status['overall_completion']}%")
        print(f"   Auto-complete enabled: {status['can_auto_complete']}")

        return True

    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Function test failed: {e}")
        return False


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("  Smart Setup Assistant - Integration Test Suite")
    print("=" * 60)

    tests = [
        ("Module Imports", test_imports),
        ("Blueprint Registration", test_blueprint_registration),
        ("App Creation & Routes", test_app_creation),
        ("Template Existence", test_template_exists),
        ("Navigation Link", test_navigation_link),
        ("Status Analysis Logic", test_analyze_setup_status),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("  Test Results Summary")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {test_name}")

    print("=" * 60)
    print(f"  {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.0f}%)")
    print("=" * 60)

    if passed_count == total_count:
        print("\n🎉 All tests passed! Smart Setup is ready to use.")
        print("\nNext steps:")
        print("1. Start the Flask app: python scripts/web_app.py")
        print("2. Visit: http://localhost:5000/smart-setup")
        print("3. Follow the Quick Configuration workflow")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review errors above.")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
