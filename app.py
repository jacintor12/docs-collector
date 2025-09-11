print('Starting app.py...', flush=True)
import scripts.email_to_smartsheet

if __name__ == "__main__":
	scripts.email_to_smartsheet.process_incoming_emails()
