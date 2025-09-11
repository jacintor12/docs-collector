import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# --- NEW: Import MIMEApplication to handle the original email as an attachment ---
from email.mime.application import MIMEApplication

# --- CONFIGURATION: FILL IN YOUR DETAILS HERE ---

# -- Source Account (where to check for unread mail) --
IMAP_SERVER = 'outlook.office365.com'
IMAP_PORT = 993
IMAP_USER = 'hialeah@lemus.org'
IMAP_PASSWORD = 'Teamcolombia20252025!' # IMPORTANT: Use an App Password

# -- Destination (where to forward the email) --
FORWARD_TO_ADDRESS = 'jacintor12@gmail.com'

# -- Sending Account (which account to use to send the forward) --
SMTP_SERVER = 'smtp.office365.com'
SMTP_PORT = 587
SMTP_USER = 'hialeah@lemus.org'
SMTP_PASSWORD = 'Teamcolombia20252025!'


def process_mailbox():
    """
    Connects to the IMAP server, finds unread emails, and forwards them.
    """
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(IMAP_USER, IMAP_PASSWORD)
        mail.select('inbox')

        status, message_ids = mail.search(None, 'UNSEEN')
        if status != 'OK':
            print("No new messages found.")
            return

        for msg_id in message_ids[0].split():
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                continue

            raw_email_bytes = msg_data[0][1]
            msg = email.message_from_bytes(raw_email_bytes)

            print(f"Found unread email: '{msg['subject']}' from '{msg['from']}'")

            # --- MODIFIED: Pass the raw email bytes to the sending function ---
            send_forwarded_email(msg, raw_email_bytes)

            mail.store(msg_id, '+FLAGS', '\\Seen')
            print(f"Marked message {msg_id.decode()} as read.")

        mail.logout()

    except Exception as e:
        print(f"An error occurred: {e}")

# --- REVISED FUNCTION TO HANDLE ATTACHMENTS ---
def send_forwarded_email(msg, raw_email_bytes):
    """
    Recreates the original email as a new message, copying subject, body, and attachments.
    """
    new_msg = MIMEMultipart()
    new_msg['To'] = FORWARD_TO_ADDRESS
    new_msg['From'] = SMTP_USER
    new_msg['Subject'] = f"Fwd: {msg['subject']}"

    # Add a note about the original sender
    body_text = f"This message was originally sent by {msg['from']} and automatically forwarded.\n\n"

    # Extract the main body (text/plain or text/html)
    body_found = False
    for part in msg.walk():
        if part.get_content_type() == 'text/plain' and not body_found:
            body_text += part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
            body_found = True
        elif part.get_content_type() == 'text/html' and not body_found:
            # If you prefer HTML, you can use this instead
            body_text += part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
            body_found = True
    new_msg.attach(MIMEText(body_text, 'plain'))

    # Attach all original attachments
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        filename = part.get_filename()
        if filename:
            attachment = MIMEApplication(part.get_payload(decode=True), Name=filename)
            attachment['Content-Disposition'] = f'attachment; filename="{filename}"'
            new_msg.attach(attachment)

    # Send the recreated email via SMTP
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, FORWARD_TO_ADDRESS, new_msg.as_string())
            print(f"Successfully sent recreated email with attachments to {FORWARD_TO_ADDRESS}")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == '__main__':
    print(f"Checking for new emails to forward at {IMAP_USER}...")
    process_mailbox()
    print("Done.")