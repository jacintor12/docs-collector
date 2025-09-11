
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import CallMetric

app = create_app()

with app.app_context():
    metrics = CallMetric.query.all()
    for m in metrics:
        print(f"ID: {m.id}, Week Start: {m.week_start_date}, Completed: {m.completed_calls}, Missed: {m.missed_calls}, Avg Duration: {m.avg_duration}")
