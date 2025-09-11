import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Case

app = create_app()

with app.app_context():
    cases_to_delete = Case.query.filter((Case.case_number == None) | (Case.case_number == '')).all()
    for case in cases_to_delete:
        print(f"Deleting case_id: {case.case_id}, client: {case.client_name}, email: {case.client_email}")
        db.session.delete(case)
    db.session.commit()
    print(f"Deleted {len(cases_to_delete)} cases with NULL or empty case_number.")
