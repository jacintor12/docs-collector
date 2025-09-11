
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Case
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    case = Case(
        client_name='Test Client',
        client_email='jacintor1@aol.com',
        request_date=datetime.now(),
        deadline_date=datetime.now() + timedelta(days=3)
    )
    db.session.add(case)
    db.session.commit()
    print(f"Test case created with case_id: {case.case_id}")
