from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UserAction(db.Model):
    __tablename__ = "user_actions"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.String(128))
    service = db.Column(db.String(50))
    endpoint = db.Column(db.String(128))
    action_type = db.Column(db.String(128))
    request_data = db.Column(db.Text)
    response_summary = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))

