from app import db

class Case(db.Model):
    case_id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=True)  # User-defined case number
    client_name = db.Column(db.String(120), nullable=False)
    client_email = db.Column(db.String(120), nullable=False)
    request_date = db.Column(db.DateTime, nullable=False)
    deadline_date = db.Column(db.DateTime, nullable=False)
    visible = db.Column(db.Boolean, default=True)
    description = db.Column(db.String(255), default='')
    documents = db.relationship('Document', backref='case', lazy=True)

class Document(db.Model):
    document_id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.case_id'), nullable=False)
    document_name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), nullable=False) # 'Requested' or 'Received'
    received_date = db.Column(db.DateTime)

class CallMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_start_date = db.Column(db.DateTime, nullable=False)
    completed_calls = db.Column(db.Integer, default=0)
    missed_calls = db.Column(db.Integer, default=0)
    avg_duration = db.Column(db.Float, default=0.0)
