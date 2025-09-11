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
IMAP_USER = 'hialeah@lemus.org'
IMAP_PASSWORD = 'Teamcolombia20252025!' # IMPORTANT: Use an App Password

# -- Destination (where to forward the email) --
FORWARD_TO_ADDRESS = 'jacintor12@gmail.com'

# -- Sending Account (which account to use to send the forward) --
SMTP_SERVER = 'smtp.office365.com'
SMTP_PORT = 587
SMTP_USER = 'hialeah@lemus.org
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
    Constructs a new email that contains the original email as an attachment.
    """
    # Create a new container message
    forwarded_msg = MIMEMultipart()
    forwarded_msg['To'] = FORWARD_TO_ADDRESS
    forwarded_msg['From'] = SMTP_USER
    forwarded_msg['Subject'] = f"Fwd: {msg['subject']}"

    # Add a simple text body explaining the forward.
    body_text = "This is an automatically forwarded message."
    forwarded_msg.attach(MIMEText(body_text, 'plain'))
    
    # Create an attachment from the original raw email bytes
    original_as_attachment = MIMEApplication(raw_email_bytes, _subtype="rfc822")
    original_as_attachment.add_header('Content-Disposition', 'attachment', filename="original_email.eml")
    
    # Attach the original email to our new container message
    forwarded_msg.attach(original_as_attachment)

    # Send the email via SMTP
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, FORWARD_TO_ADDRESS, forwarded_msg.as_string())
            print(f"Successfully forwarded email with attachments to {FORWARD_TO_ADDRESS}")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == '__main__':
    print(f"Checking for new emails to forward at {IMAP_USER}...")
    process_mailbox()
    print("Done.")