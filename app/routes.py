from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, session
import os
import json
import threading
import uuid

routes = Blueprint('routes', __name__)

# Global progress and results store
UPLOAD_PROGRESS = {}
UPLOAD_RESULTS = {}

@routes.route('/results/<upload_id>')
def results(upload_id):
    # Wait for completion if needed
    import time
    for _ in range(60):  # Wait up to 60 seconds
        progress = UPLOAD_PROGRESS.get(upload_id, {})
        results = UPLOAD_RESULTS.get(upload_id, {})
        if progress.get('done') and results and 'summary' in results:
            return render_template('results.html', result={'summary': results['summary'], 'upload_id': upload_id})
        time.sleep(1)
    # Timeout: show waiting message
    return render_template('results.html', result={'summary': None, 'upload_id': upload_id})

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, session
import os
import json
import threading
import uuid

routes = Blueprint('routes', __name__)

# Global progress and results store
UPLOAD_PROGRESS = {}
UPLOAD_RESULTS = {}

@routes.route('/results/<upload_id>')
def results(upload_id):
    # Wait for completion if needed
    import time
    for _ in range(60):  # Wait up to 60 seconds
        progress = UPLOAD_PROGRESS.get(upload_id, {})
        results = UPLOAD_RESULTS.get(upload_id, {})
        if progress.get('done') and results and 'summary' in results:
            return render_template('results.html', result={'summary': results['summary'], 'upload_id': upload_id})
        time.sleep(1)
    # Timeout: show waiting message
    return render_template('results.html', result={'summary': None, 'upload_id': upload_id})

@routes.route('/progress/<upload_id>')
def get_progress(upload_id):
    progress = UPLOAD_PROGRESS.get(upload_id, {'current': 0, 'total': 0, 'done': False})
    results = UPLOAD_RESULTS.get(upload_id, [])
    if progress.get('done') and isinstance(results, dict):
        progress['results'] = results.get('results', [])
        progress['summary'] = results.get('summary', {})
    else:
        progress['results'] = []
        progress['summary'] = {}
    print(f"Progress poll for {upload_id}: current={progress['current']}, total={progress['total']}, done={progress['done']}, summary={progress['summary']}")
    return jsonify(progress)

# Smartsheet CSV Uploader page route
@routes.route('/csv-uploader')
def csv_uploader():
    return render_template('csv_uploader.html')

# Reports page: list failed email alerts
@routes.route('/reports', methods=['GET'])
def reports():
    try:
        with open('documents/failed_alerts.json', 'r') as f:
            alerts = json.load(f)
    except Exception:
        alerts = []
    return render_template('reports.html', alerts=alerts)

# Clear single alert
@routes.route('/clear-alert/<int:alert_id>', methods=['POST'])
def clear_alert(alert_id):
    try:
        with open('documents/failed_alerts.json', 'r+') as f:
            alerts = json.load(f)
            if 0 <= alert_id < len(alerts):
                alerts.pop(alert_id)
                f.seek(0)
                f.truncate()
                json.dump(alerts, f, indent=2)
    except Exception as e:
        print(f"Error clearing alert: {e}")
    return redirect(url_for('routes.reports'))

# Clear all alerts
@routes.route('/clear-all-alerts', methods=['POST'])
def clear_all_alerts():
    try:
        with open('documents/failed_alerts.json', 'w') as f:
            json.dump([], f)
    except Exception as e:
        print(f"Error clearing all alerts: {e}")
    return redirect(url_for('routes.reports'))

# Email Actions page route
@routes.route('/email-actions')
def email_actions():
    return render_template('email_actions.html')

# Run Now route
@routes.route('/run-now', methods=['POST'])
def run_now():
    try:
        from scripts.email_to_smartsheet import process_incoming_emails
        process_incoming_emails()
        return {'message': 'Email extraction triggered!'}
    except Exception as e:
        return {'message': f'Error running email extraction: {str(e)}'}, 500

# Sync Email route
@routes.route('/sync-email', methods=['POST'])
def sync_email():
    try:
        from scripts.email_to_smartsheet import process_incoming_emails
        process_incoming_emails()
        return {'message': 'Email sync completed successfully.'}
    except Exception as e:
        return {'message': f'Error syncing email: {str(e)}'}, 500


# Email config helpers
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/email_config.json'))

def load_email_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_email_config(data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f)

# Config route
@routes.route('/config', methods=['GET', 'POST'])
def config():
    message = None
    if request.method == 'POST':
        imap_server = request.form.get('imap_server')
        email_user = request.form.get('email_user')
        email_pass = request.form.get('email_pass')
        forward_to_email = request.form.get('forward_to_email', '')
        save_email_config({
            'IMAP_SERVER': imap_server,
            'EMAIL_USER': email_user,
            'EMAIL_PASS': email_pass,
            'FORWARD_TO_EMAIL': forward_to_email
        })
        message = 'Credentials saved successfully.'
    config = load_email_config()
    return render_template('config.html', message=message, **config)

# Index route
@routes.route('/')
def index():
    return render_template('index.html')

@routes.route('/upload', methods=['POST'])
def upload_csv():
    from werkzeug.utils import secure_filename
    import pandas as pd
    import smartsheet
    access_token = request.form.get('access_token')
    sheet_id = request.form.get('sheet_id')
    file = request.files.get('file')
    if not file or not access_token or not sheet_id:
        flash('Missing required fields or file.')
        return redirect(url_for('routes.csv_uploader'))
    filename = secure_filename(file.filename)
    upload_path = os.path.join('documents', filename)
    file.save(upload_path)
    # Read CSV columns
    try:
        df = pd.read_csv(upload_path)
        csv_cols = list(df.columns)
    except Exception as e:
        flash(f'Error reading CSV: {e}')
        return redirect(url_for('routes.csv_uploader'))
    # Fetch Smartsheet columns dynamically
    try:
        smartsheet_client = smartsheet.Smartsheet(access_token)
        sheet = smartsheet_client.Sheets.get_sheet(sheet_id)
        smartsheet_cols = {col.title: col.id for col in sheet.columns}
    except Exception as e:
        flash(f'Error fetching Smartsheet columns: {e}')
        smartsheet_cols = {}
    # Attempt auto-mapping by name
    auto_mapping = {col: smartsheet_cols.get(col, "") for col in csv_cols}
    return render_template(
        'mapping.html',
        access_token=access_token,
        sheet_id=sheet_id,
        filename=filename,
        csv_cols=csv_cols,
        smartsheet_cols=smartsheet_cols,
        auto_mapping=auto_mapping
    )

@routes.route('/update', methods=['POST'])
def update_sheet():
    import pandas as pd
    import smartsheet
    from datetime import datetime
    import re
    import time
    access_token = request.form.get('access_token')
    sheet_id = request.form.get('sheet_id')
    filename = request.form.get('filename')
    unique_identifier = request.form.get('unique_identifier')
    upload_id = str(uuid.uuid4())
    session['upload_id'] = upload_id
    # Build mapping from form
    csv_to_smartsheet = {}
    for key in request.form:
        if key.startswith('map_'):
            csv_col = key[4:]
            smartsheet_col_id = request.form.get(key)
            if smartsheet_col_id:
                csv_to_smartsheet[csv_col] = smartsheet_col_id
    # Load CSV
    csv_path = os.path.join('documents', filename)
    try:
        df = pd.read_csv(csv_path)
        # Robust cleaning: strip whitespace from all string columns
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
    except Exception as e:
        result = {'error': f'Error reading CSV: {e}'}
        return render_template('results.html', result=result)
    # Connect to Smartsheet
    try:
        smartsheet_client = smartsheet.Smartsheet(access_token)
        # Set a 30-second timeout for all API requests
        smartsheet_client.timeout = 30
        sheet = smartsheet_client.Sheets.get_sheet(sheet_id)
        col_types = {col.id: col.type for col in sheet.columns}
        unique_col_id = None
        if unique_identifier:
            for col in sheet.columns:
                if col.title == unique_identifier:
                    unique_col_id = col.id
                    break
        existing_ids = {}
        if unique_col_id:
            for s_row in sheet.rows:
                for cell in s_row.cells:
                    if cell.column_id == unique_col_id and cell.value is not None:
                        existing_ids[str(cell.value)] = s_row.id
        print(f"Loaded {len(existing_ids)} existing IDs from Smartsheet.")
    except Exception as e:
        result = {'error': f'Error connecting to Smartsheet: {e}'}
        return render_template('results.html', result=result)
    # Prepare rows for update/insert
    results = []
    total_rows = len(df)
    UPLOAD_PROGRESS[upload_id] = {'current': 0, 'total': total_rows, 'done': False}
    
    # Helper: powerful date parser
    def parse_date(value):
        value_str = str(value).strip()
        try:
            dt = pd.to_datetime(value_str, errors='raise')
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})', value_str)
        if match:
            m, d, y = match.groups()
            if len(y) == 2:
                y = '20' + y if int(y) < 50 else '19' + y
            try:
                dt = datetime(int(y), int(m), int(d))
                return dt.strftime('%Y-%m-%d')
            except Exception:
                pass
        return value_str

    def process_rows():
        inserted = 0
        updated = 0
        skipped = 0
        try:
            for idx, row in enumerate(df.iterrows()):
                # Move progress update to the top of the loop
                UPLOAD_PROGRESS[upload_id]['current'] = idx
                _, row = row
                cells = []
                for csv_col, smartsheet_col_id in csv_to_smartsheet.items():
                    value = row.get(csv_col, None)
                    col_type = col_types.get(int(smartsheet_col_id), None)
                    if col_type == 'DATE' and value:
                        value = parse_date(value)
                    if col_type == 'CHECKBOX' and value is not None:
                        value_str = str(value).strip().lower()
                        if value_str in ['true', 'yes', '1', 'y', 'checked']:
                            value = True
                        elif value_str in ['false', 'no', '0', 'n', 'unchecked', '']:
                            value = False
                        else:
                            value = False
                    if col_type == 'TEXT_NUMBER' and value is not None:
                        try:
                            value_str = str(value).replace(',', '').strip()
                            if value_str.isdigit():
                                value = int(value_str)
                            else:
                                value = float(value_str)
                        except Exception:
                            pass
                    cell = smartsheet.models.Cell()
                    cell.column_id = int(smartsheet_col_id)
                    cell.value = value
                    cells.append(cell)
                match_row_id = None
                if unique_identifier and unique_identifier in row:
                    identifier_value = str(row[unique_identifier])
                    match_row_id = existing_ids.get(identifier_value)
                if match_row_id:
                    # Already exists, update
                    new_row = smartsheet.models.Row()
                    new_row.id = match_row_id
                    new_row.cells = cells
                    try:
                        response = smartsheet_client.Sheets.update_rows(sheet_id, [new_row])
                        updated += 1
                        results.append({'contact': row.to_dict(), 'result': response.message, 'action': 'updated'})
                    except Exception as e:
                        results.append({'contact': row.to_dict(), 'result': f'Error updating: {e}', 'action': 'error'})
                else:
                    # Not in sheet, insert
                    print(f"Attempting to insert new row with identifier '{row.get(unique_identifier)}'")
                    new_row = smartsheet.models.Row()
                    new_row.to_top = True
                    new_row.sheet_id = int(sheet_id)
                    new_row.cells = cells
                    try:
                        response = smartsheet_client.Sheets.add_rows(sheet_id, [new_row])
                        print(f"Insert response: {response.message}")
                        inserted += 1
                        results.append({'contact': row.to_dict(), 'result': response.message, 'action': 'inserted'})
                    except Exception as e:
                        print(f"Error inserting row with identifier '{row.get(unique_identifier)}': {e}")
                        results.append({'contact': row.to_dict(), 'result': f'Error inserting: {e}', 'action': 'error'})
                # After each row insert/update, sleep to respect Smartsheet API rate limits
                time.sleep(0.35)
        finally:
            skipped = total_rows - inserted - updated
            UPLOAD_PROGRESS[upload_id]['current'] = total_rows
            UPLOAD_PROGRESS[upload_id]['done'] = True
            UPLOAD_RESULTS[upload_id] = {
                'results': results,
                'summary': {
                    'inserted': inserted,
                    'updated': updated,
                    'skipped': skipped,
                    'total': total_rows
                }
            }
    threading.Thread(target=process_rows).start()
    # Redirect to results page for this upload
    return redirect(url_for('routes.results', upload_id=upload_id))
