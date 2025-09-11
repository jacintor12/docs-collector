from apscheduler.schedulers.background import BackgroundScheduler
from scripts.check_emails import main as check_emails_main
from scripts.process_calls import main as process_calls_main

scheduler = BackgroundScheduler()
scheduler.add_job(check_emails_main, 'interval', minutes=5)
scheduler.add_job(process_calls_main, 'interval', days=1)

scheduler.start()

# ...existing code...
