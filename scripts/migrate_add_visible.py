import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    result = db.session.execute(text("PRAGMA table_info('case')"))
    columns = [row[1] for row in result]
    if 'visible' not in columns:
        db.session.execute(text('ALTER TABLE "case" ADD COLUMN visible BOOLEAN DEFAULT 1'))
        print('visible column added.')
    else:
        print('visible column already exists.')
