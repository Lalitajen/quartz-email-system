#!/usr/bin/env python3
"""
Create a test customer for email tracking testing
Email: catty366336@gmail.com
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuration
SPREADSHEET_ID = "1AcXb7y4ZHwVcQ3OoMa-xUZh2xeXxSizXHiUnt9-yjSw"

def add_test_customer():
    """Add test customer to Google Sheets"""

    # Authenticate
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
    client = gspread.authorize(creds)

    # Open spreadsheet
    workbook = client.open_by_key(SPREADSHEET_ID)

    # Get or create Customers sheet
    try:
        sheet = workbook.worksheet('Customers')
    except gspread.WorksheetNotFound:
        sheet = workbook.add_worksheet(title='Customers', rows=1000, cols=20)
        # Add headers
        headers = [
            'customer_id', 'company_name', 'contact_name', 'email',
            'phone', 'country', 'industry', 'pipeline_stage',
            'engagement_level', 'research_status', 'research_summary',
            'last_contact', 'notes', 'created_at'
        ]
        sheet.append_row(headers)

    # Check if customer already exists
    try:
        cell = sheet.find('catty366336@gmail.com')
        if cell:
            print(f"✅ Test customer already exists at row {cell.row}")
            return
    except:
        pass

    # Create test customer data
    customer_data = [
        'TEST001',  # customer_id
        'Catty Test Company',  # company_name
        'Catty Test',  # contact_name
        'catty366336@gmail.com',  # email
        '+1-555-0001',  # phone
        'United States',  # country
        'Glass Manufacturing',  # industry
        '1',  # pipeline_stage (1 = Prospecting)
        'NEW',  # engagement_level
        'Pending',  # research_status
        '',  # research_summary
        datetime.now().strftime('%Y-%m-%d'),  # last_contact
        'Test customer for email tracking system',  # notes
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # created_at
    ]

    # Add customer
    sheet.append_row(customer_data)
    print("✅ Test customer created successfully!")
    print("\n📧 Test Customer Details:")
    print(f"   Company: Catty Test Company")
    print(f"   Email: catty366336@gmail.com")
    print(f"   Pipeline Stage: 1 (Prospecting)")
    print(f"   Status: NEW")
    print("\n🎯 Next Steps:")
    print("   1. Go to: http://localhost:5000/customers")
    print("   2. You should see 'Catty Test Company' in the list")
    print("   3. Go to: http://localhost:5000/compose")
    print("   4. Select 'Catty Test Company' from dropdown")
    print("   5. Click 'Generate Email' to create AI email")
    print("   6. Click 'Send Email' to send test email")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Creating Test Customer for Email Tracking")
    print("="*60 + "\n")

    try:
        add_test_customer()
        print("\n" + "="*60)
        print("  ✓ Test customer setup complete!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check service_account.json exists")
        print("2. Verify Google Sheets ID is correct")
        print("3. Ensure service account has access to sheet")
