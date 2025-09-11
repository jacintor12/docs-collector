import smartsheet
import os

# --- CONFIG ---
SHEET_ID = 5289204201246596  # <-- Updated to match email attachment script
DOCS_RECEIVED_COL_ID = 3016977588899716  # "Docs Received" column ID

# Optionally, get from environment or config
SHEET_ID = int(os.getenv('SMARTSHEET_SHEET_ID', SHEET_ID))
ACCESS_TOKEN = os.getenv('SMARTSHEET_ACCESS_TOKEN')
if not ACCESS_TOKEN:
    raise RuntimeError("SMARTSHEET_ACCESS_TOKEN environment variable not set.")

# --- MAIN LOGIC ---
def main():
    smart = smartsheet.Smartsheet(ACCESS_TOKEN)
    smart.errors_as_exceptions(True)
    print(f"Fetching sheet {SHEET_ID}...")
    sheet = smart.Sheets.get_sheet(SHEET_ID)
    print(f"Found {len(sheet.rows)} rows.")
    updates = []
    for row in sheet.rows:
        # Fetch row details including attachments
        row_details = smart.Sheets.get_row(SHEET_ID, row.id, include=['attachments'])
        attachment_count = len(getattr(row_details, 'attachments', []))
        print(f"Row {row.id}: {attachment_count} attachments.")
        # Prepare cell update for Docs Received column
        cell = smartsheet.models.Cell()
        cell.column_id = DOCS_RECEIVED_COL_ID
        cell.value = attachment_count
        new_row = smartsheet.models.Row()
        new_row.id = row.id
        new_row.cells = [cell]
        updates.append(new_row)
    # Batch update rows (Smartsheet API allows up to 500 rows per request)
    print(f"Updating {len(updates)} rows...")
    for i in range(0, len(updates), 500):
        batch = updates[i:i+500]
        response = smart.Sheets.update_rows(SHEET_ID, batch)
        print(f"Batch {i//500+1}: {response.message}")
    print("Done.")

if __name__ == "__main__":
    main()
