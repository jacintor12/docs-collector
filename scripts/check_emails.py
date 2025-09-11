
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import imaplib
import email
from email.header import decode_header
from app import create_app, db
from app.models import Case, Document
from scripts import config

def process_attachments(msg, case):
	for part in msg.walk():
		if part.get_content_maintype() == 'multipart':
			continue
		if part.get('Content-Disposition') is None:
			continue
		filename = part.get_filename()
		if filename:
			filename = decode_header(filename)[0][0]
			if isinstance(filename, bytes):
				filename = filename.decode()
			# Save file to documents/case_{case.case_id}/
			case_dir = os.path.join('documents', f'case_{case.case_id}')
			os.makedirs(case_dir, exist_ok=True)
			filepath = os.path.join(case_dir, filename)
			with open(filepath, 'wb') as f:
				f.write(part.get_payload(decode=True))
			# Update DB
			doc = Document.query.filter_by(case_id=case.case_id, document_name=filename).first()
			if doc:
				doc.status = 'Received'
				db.session.commit()

def main():
	app = create_app()
	with app.app_context():
		mail = imaplib.IMAP4_SSL(config.IMAP_SERVER)
		mail.login(config.EMAIL_USER, config.EMAIL_PASS)
		mail.select('inbox')
		# Search for unread emails
		status, messages = mail.search(None, '(UNSEEN)')
		for num in messages[0].split():
			status, data = mail.fetch(num, '(RFC822)')
			msg = email.message_from_bytes(data[0][1])
			sender = email.utils.parseaddr(msg.get('From'))[1]
			# Find case by sender
			case = Case.query.filter_by(client_email=sender).first()
			if case:
				process_attachments(msg, case)
		mail.logout()

if __name__ == '__main__':
	main()
