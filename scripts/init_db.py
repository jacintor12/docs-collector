
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Case, Document, CallMetric


app = create_app()

with app.app_context():
    print('SQLAlchemy metadata tables:', db.metadata.tables.keys())
    try:
        db.create_all()
        print("Database tables created successfully in:", app.config['SQLALCHEMY_DATABASE_URI'])
    except Exception as e:
        print("Error creating tables:", e)
