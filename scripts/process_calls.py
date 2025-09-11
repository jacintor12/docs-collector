
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from datetime import datetime
from app import create_app, db
from app.models import CallMetric

def process_csv(csv_path):
	df = pd.read_csv(csv_path)
	# Example columns: 'CallStatus', 'Duration', 'Timestamp'
	week_start = df['Timestamp'].min()
	completed = df[df['CallStatus'] == 'Completed'].shape[0]
	missed = df[df['CallStatus'] == 'Missed'].shape[0]
	avg_duration = df['Duration'].mean() if not df.empty else 0
	metric = CallMetric(
		week_start_date=datetime.strptime(week_start, '%Y-%m-%d'),
		completed_calls=completed,
		missed_calls=missed,
		avg_duration=avg_duration
	)
	db.session.add(metric)
	db.session.commit()

def main():
	app = create_app()
	with app.app_context():
		# Find latest CSV in documents/
		csv_files = [f for f in os.listdir('documents') if f.endswith('.csv')]
		if not csv_files:
			print('No CSV files found.')
			return
		latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join('documents', x)))
		process_csv(os.path.join('documents', latest_csv))

if __name__ == '__main__':
	main()
