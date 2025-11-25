from app.services.google_sheets.google_sheets_service import GoogleSheetsService
from app.services.google_sheets.asset_allocation_parser import AssetAllocationParser 

ASSET_ALLOCATION_INITIAL_ROW = 7
ASSET_ALLOCATION_SUMMARY_ROW = 22

google_client = GoogleSheetsService()
parser = AssetAllocationParser()

data = google_client.fetch_spreadsheet_rows("Rodrigo Vanzelotti", skip_initial_rows=ASSET_ALLOCATION_INITIAL_ROW)
# asset_allocation_summary = parser._parse_general_allocation(data['Asset Allocation'][:ASSET_ALLOCATION_SUMMARY_ROW])
al_detail, al_summary = parser.parse_general_allocation(data['Asset Allocation'][:ASSET_ALLOCATION_SUMMARY_ROW])
subtables = parser.parse_multiple_tables(data['Asset Allocation'])