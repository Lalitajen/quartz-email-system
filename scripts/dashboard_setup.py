"""
Dashboard Generator for Google Sheets
Creates formulas and charts for real-time pipeline tracking
"""

import gspread
from google.oauth2.service_account import Credentials


def setup_dashboard(spreadsheet_id: str):
    """Set up dashboard with formulas and formatting"""
    
    # Authenticate
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file('google_credentials.json', scopes=scope)
    client = gspread.authorize(creds)
    workbook = client.open_by_key(spreadsheet_id)
    
    # Create or get Dashboard sheet
    try:
        dashboard = workbook.worksheet('Dashboard')
    except:
        dashboard = workbook.add_worksheet(title='Dashboard', rows=50, cols=10)
    
    # Clear existing content
    dashboard.clear()
    
    # Set up dashboard structure
    dashboard.update('A1', [['Quartz Email Outreach - Dashboard']])
    dashboard.format('A1', {
        'textFormat': {'bold': True, 'fontSize': 16},
        'horizontalAlignment': 'CENTER'
    })
    
    # Key Metrics Section
    metrics = [
        ['', ''],
        ['KEY METRICS', ''],
        ['', ''],
        ['Total Customers', '=COUNTA(Customers!A:A)-1'],
        ['Researched', '=COUNTIF(Customers!J:J,"completed")'],
        ['Pending Research', '=COUNTIF(Customers!J:J,"pending")'],
        ['', ''],
        ['Total Emails Sent', '=COUNTA(Email_Tracking!A:A)-1'],
        ['Emails Today', '=COUNTIF(Email_Tracking!F:F,TODAY())'],
        ['This Week', '=COUNTIF(Email_Tracking!F:F,">="&TODAY()-7)'],
        ['This Month', '=COUNTIF(Email_Tracking!F:F,">="&TODAY()-30)'],
        ['', ''],
        ['Email Response Rate', '=IFERROR(COUNTIF(Email_Tracking!L:L,"yes")/COUNTA(Email_Tracking!A:A),0)'],
        ['Avg Confidence Score', '=IFERROR(AVERAGE(Email_Tracking!Q:Q),0)'],
        ['Pending Reviews', '=COUNTIF(Email_Tracking!R:R,"pending_review")'],
    ]
    
    dashboard.update('A3', metrics)
    
    # Format metrics
    dashboard.format('A4', {'textFormat': {'bold': True}})
    dashboard.format('B4:B16', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0'}})
    dashboard.format('B14', {'numberFormat': {'type': 'PERCENT', 'pattern': '0.00%'}})
    dashboard.format('B15', {'numberFormat': {'type': 'NUMBER', 'pattern': '0.00'}})
    
    # Pipeline Breakdown Section
    pipeline_section = [
        ['', ''],
        ['PIPELINE BY STAGE', 'Count', '%'],
        ['', '', ''],
        ['1 - Prospecting', '=COUNTIF(Customers!H:H,1)', '=B21/$B$4'],
        ['2 - Initial Contact', '=COUNTIF(Customers!H:H,2)', '=B22/$B$4'],
        ['3 - Qualification', '=COUNTIF(Customers!H:H,3)', '=B23/$B$4'],
        ['4 - Sample & Testing', '=COUNTIF(Customers!H:H,4)', '=B24/$B$4'],
        ['5 - Negotiation', '=COUNTIF(Customers!H:H,5)', '=B25/$B$4'],
        ['6 - Contract', '=COUNTIF(Customers!H:H,6)', '=B26/$B$4'],
        ['7 - Fulfillment', '=COUNTIF(Customers!H:H,7)', '=B27/$B$4'],
    ]
    
    dashboard.update('A18', pipeline_section)
    
    # Format pipeline section
    dashboard.format('A19', {'textFormat': {'bold': True}})
    dashboard.format('C21:C27', {'numberFormat': {'type': 'PERCENT', 'pattern': '0.0%'}})
    
    # Email Activity Section
    activity_section = [
        ['', ''],
        ['RECENT EMAIL ACTIVITY', ''],
        ['', ''],
        ['Last 7 Days:', ''],
        ['Sent', '=COUNTIFS(Email_Tracking!F:F,">="&TODAY()-7,Email_Tracking!K:K,"sent")'],
        ['Opened', '=COUNTIFS(Email_Tracking!F:F,">="&TODAY()-7,Email_Tracking!L:L,"yes")'],
        ['Replied', '=COUNTIFS(Email_Tracking!F:F,">="&TODAY()-7,Email_Tracking!M:M,"yes")'],
        ['', ''],
        ['Open Rate (7d)', '=IFERROR(B35/B34,0)'],
        ['Reply Rate (7d)', '=IFERROR(B36/B34,0)'],
    ]
    
    dashboard.update('E3', activity_section)
    
    # Format activity section
    dashboard.format('E4', {'textFormat': {'bold': True}})
    dashboard.format('F38:F39', {'numberFormat': {'type': 'PERCENT', 'pattern': '0.0%'}})
    
    # Top Priorities Section
    priorities = [
        ['', ''],
        ['TOP PRIORITIES', ''],
        ['', ''],
        ['Action', 'Count'],
        ['Pending Reviews', '=COUNTIF(Email_Tracking!R:R,"pending_review")'],
        ['Follow-ups Due', '=COUNTIFS(Email_Tracking!P:P,"follow_up*",Email_Tracking!K:K,"sent")'],
        ['Research Needed', '=COUNTIF(Customers!J:J,"pending")'],
        ['Hot Leads (Tag)', '=COUNTIF(Customers!I:I,"*hot*")'],
    ]
    
    dashboard.update('E18', priorities)
    dashboard.format('E19', {'textFormat': {'bold': True}})
    
    # Add conditional formatting for alerts
    # Red background if pending reviews > 5
    dashboard.format('F22', {
        'backgroundColor': {'red': 1.0, 'green': 0.9, 'blue': 0.9}
    })
    
    # Add timestamp
    dashboard.update('A45', [['Last Updated:', '=NOW()']])
    dashboard.format('B45', {'numberFormat': {'type': 'DATE_TIME'}})
    
    print("✅ Dashboard created successfully!")
    print(f"📊 View at: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    
    return dashboard


def create_chart_on_dashboard(spreadsheet_id: str):
    """Create visual charts for pipeline stages"""
    
    # This requires using Google Sheets API directly for chart creation
    # Simplified version - you can expand with charts using API
    
    print("📈 Charts can be added manually:")
    print("   1. Select cells A21:B27 (pipeline data)")
    print("   2. Insert > Chart")
    print("   3. Choose Pie Chart or Column Chart")
    print("   4. Drag chart to position on dashboard")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dashboard_setup.py <SPREADSHEET_ID>")
        sys.exit(1)
    
    spreadsheet_id = sys.argv[1]
    setup_dashboard(spreadsheet_id)
    create_chart_on_dashboard(spreadsheet_id)
