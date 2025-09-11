import imaplib
import email
import smartsheet
import os
import json

# Load email configuration from JSON file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/email_config.json')

def load_email_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

email_config = load_email_config()

# Email setup
IMAP_SERVER = email_config['IMAP_SERVER']
EMAIL_USER = email_config['EMAIL_USER']
EMAIL_PASS = email_config['EMAIL_PASS']

# Smartsheet setup
SMARTSHEET_TOKEN = "cJfxMwVGXUvXotLJKadJPLMuAr0oqdU32y4SS"
SHEET_ID = 5289204201246596
MATTER_ID_COL_ID = 649627317260164

smartsheet_client = smartsheet.Smartsheet(SMARTSHEET_TOKEN)

def find_row_by_matter_id(sheet_id, matter_id, matter_id_col_id):
    sheet = smartsheet_client.Sheets.get_sheet(sheet_id)
    # print(f"Searching for Matter ID: {matter_id}")
    found_ids = []
    for row in sheet.rows:
        for cell in row.cells:
            if cell.column_id == matter_id_col_id:
                # print(f"Row {row.id} - Matter ID value: {cell.value}")
                found_ids.append(cell.value)
                try:
                    if float(cell.value) == float(matter_id):
                        # print(f"Match found in row {row.id}")
                        return row.id
                except (ValueError, TypeError):
                    pass
    # print(f"All Matter ID values found: {found_ids}")
    return None

def attach_document_to_row(sheet_id, row_id, file_path):
    smartsheet_client.Attachments.attach_file_to_row(
        sheet_id, row_id, (file_path, open(file_path, 'rb'), 'application/octet-stream')
    )

def extract_matter_id(subject, body=None):
    import re
    # Flexible regex: look for any case of 'id' or 'matter id' followed by a number
    patterns = [
        r"(?i)matter[\s_-]*id[:\s-]*([0-9]+)",  # matter id, any case, spaces, dash, colon
        r"(?i)id[:\s-]*([0-9]+)"  # id, any case, spaces, dash, colon
    ]
    for pattern in patterns:
        match = re.search(pattern, subject or "")
        if match:
            return match.group(1)
        if body:
            match = re.search(pattern, body)
            if match:
                return match.group(1)
    return None

def get_client_emails_from_smartsheet(sheet_id, email_col_title="Email"):
    # Fetch all client emails from Smartsheet
    sheet = smartsheet_client.Sheets.get_sheet(sheet_id)
    email_col_id = None
    for col in sheet.columns:
        if col.title.lower() == email_col_title.lower():
            email_col_id = col.id
            break
    if not email_col_id:
        return set()
    client_emails = set()
    for row in sheet.rows:
        for cell in row.cells:
            if cell.column_id == email_col_id and cell.value:
                client_emails.add(str(cell.value).strip().lower())
    return client_emails

def process_incoming_emails():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    print("Connected to email server successfully.", flush=True)
    # List available folders for debug
    typ, folders = mail.list()
    print("Available folders:", flush=True)
    if typ == 'OK' and folders:
        for folder in folders:
            print(folder.decode(), flush=True)
    # Explicitly select 'INBOX' (case-sensitive)
    typ, mailbox_info = mail.select('INBOX')
    print(f"Selected folder 'INBOX': {typ}, {mailbox_info}", flush=True)
    typ, data = mail.search(None, 'UNSEEN')
    unseen = data[0].split()
    processed = False
    client_emails = get_client_emails_from_smartsheet(SHEET_ID)
    print(f"Found {len(unseen)} unseen emails.", flush=True)
    if not unseen:
        print("No unseen emails found.", flush=True)
    else:
        for num in unseen:
            typ, msg_data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg['subject']
            sender = email.utils.parseaddr(msg.get('From', ''))[1].strip().lower()
            print(f"Processing email from {sender} with subject: {subject}", flush=True)
            # Get body text
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode(errors='ignore')
            else:
                body = msg.get_payload(decode=True).decode(errors='ignore')

            # Try to extract client email from body if sender not in client list
            effective_sender = sender
            if sender not in client_emails:
                import re
                # Look for email addresses in the body
                found_emails = re.findall(r'[\w\.-]+@[\w\.-]+', body)
                for e in found_emails:
                    if e.lower() in client_emails:
                        effective_sender = e.lower()
                        print(f"Extracted client email from body: {effective_sender}", flush=True)
                        break
            # Check sender (now possibly extracted from body)
            if effective_sender not in client_emails:
                print(f"Sender {effective_sender} not in client list. Skipping.", flush=True)
                continue

            # Extract Matter ID from subject or body
            matter_id = extract_matter_id(subject, body)
            if not matter_id:
                # Try to extract Matter ID from body (for forwarded emails)
                import re
                match = re.search(r'id[:\s-]*([0-9]+)', body, re.IGNORECASE)
                if match:
                    matter_id = match.group(1)
                    print(f"Extracted Matter ID from body: {matter_id}", flush=True)
            if not matter_id:
                print("No valid Matter ID found in subject or body.", flush=True)
                # Log failed email to JSON file
                from datetime import datetime
                failed_alert = {
                    "subject": subject,
                    "from": effective_sender,
                    "date": msg.get("Date", str(datetime.now())),
                }
                try:
                    with open("documents/failed_alerts.json", "r+") as f:
                        alerts = json.load(f)
                        alerts.append(failed_alert)
                        f.seek(0)
                        json.dump(alerts, f, indent=2)
                except Exception as e:
                    print(f"Error logging failed alert: {e}", flush=True)
                continue

            # Forward the entire email with attachments if FORWARD_TO_EMAIL is set
            forward_to = email_config.get('FORWARD_TO_EMAIL', '').strip()
            if forward_to:
                try:
                    import smtplib
                    from email.mime.multipart import MIMEMultipart
                    from email.mime.text import MIMEText
                    from email.mime.base import MIMEBase
                    from email import encoders
                    # Build the forwarded message
                    fwd_msg = MIMEMultipart()
                    fwd_msg['From'] = EMAIL_USER
                    fwd_msg['To'] = forward_to
                    fwd_msg['Subject'] = f"FWD: {subject}"
                    # Add original body
                    body_text = body if body else "(No body text)"
                    fwd_msg.attach(MIMEText(body_text, 'plain'))
                    # Attach all files
                    for part in msg.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue
                        filename = part.get_filename()
                        if filename:
                            payload = part.get_payload(decode=True)
                            mime_part = MIMEBase('application', 'octet-stream')
                            mime_part.set_payload(payload)
                            encoders.encode_base64(mime_part)
                            mime_part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                            fwd_msg.attach(mime_part)
                    # Send via SMTP (using same server as IMAP)
                    smtp_server = IMAP_SERVER.replace('imap.', 'smtp.')
                    try:
                        # Try SSL first
                        with smtplib.SMTP_SSL(smtp_server, 465, timeout=20) as server:
                            server.login(EMAIL_USER, EMAIL_PASS)
                            server.sendmail(EMAIL_USER, forward_to, fwd_msg.as_string())
                        print(f"Forwarded email to {forward_to} via SSL:465", flush=True)
                    except Exception as ssl_err:
                        print(f"SSL failed: {ssl_err}. Trying STARTTLS on 587...", flush=True)
                        with smtplib.SMTP(smtp_server, 587, timeout=20) as server:
                            server.ehlo()
                            server.starttls()
                            server.login(EMAIL_USER, EMAIL_PASS)
                            server.sendmail(EMAIL_USER, forward_to, fwd_msg.as_string())
                        print(f"Forwarded email to {forward_to} via STARTTLS:587", flush=True)
                except Exception as e:
                    print(f"Error forwarding email: {e}", flush=True)
            found_attachment = False
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                filename = part.get_filename()
                if filename:
                    found_attachment = True
                    print(f"Found attachment: {filename}", flush=True)
                    file_data = part.get_payload(decode=True)
                    # Save file locally
                    with open(filename, 'wb') as f:
                        f.write(file_data)
                    # Find row in Smartsheet by Matter ID
                    row_id = find_row_by_matter_id(SHEET_ID, matter_id, MATTER_ID_COL_ID)
                    if row_id:
                        attach_document_to_row(SHEET_ID, row_id, filename)
                        print(f"Attached {filename} to row {row_id} for Matter ID {matter_id}", flush=True)
                    else:
                        print(f"Matter ID {matter_id} not found in Smartsheet.", flush=True)
                    # Optionally delete local file after upload
                    os.remove(filename)
                    processed = True
            if not found_attachment:
                print("No attachment found in this email.", flush=True)
        if processed:
            print("All unseen emails processed.", flush=True)
    print("Email to Smartsheet process completed successfully.", flush=True)

    # After syncing emails, update Docs Received count for all rows
    try:
        import subprocess
        print("Updating Docs Received counts in Smartsheet...", flush=True)
        env = os.environ.copy()
        env["SMARTSHEET_ACCESS_TOKEN"] = os.getenv("SMARTSHEET_ACCESS_TOKEN", "cJfxMwVGXUvXotLJKadJPLMuAr0oqdU32y4SS")
        result = subprocess.run([
            "python",
            "scripts/count_and_update_docs_received.py"
        ], capture_output=True, text=True, env=env)
        print(result.stdout)
        if result.stderr:
            print("Attachment count script error:", result.stderr, flush=True)
    except Exception as e:
        print(f"Failed to update Docs Received counts: {e}", flush=True)

if __name__ == "__main__":
    process_incoming_emails()
