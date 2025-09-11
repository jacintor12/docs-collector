
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Case
from sqlalchemy import text

app = create_app()


with app.app_context():
    # Check if case_number column exists
    try:
        result = db.session.execute(text("PRAGMA table_info('case')"))
        columns = [row[1] for row in result]
        if 'case_number' not in columns:
            db.session.execute(text('ALTER TABLE "case" ADD COLUMN case_number VARCHAR(50)'))
            print('case_number column added (no UNIQUE constraint).')
        else:
            print('case_number column already exists.')
    except Exception as e:
        print('Migration failed:', e)
