from app import db
from datetime import datetime


class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_transactions = db.Column(db.Integer, default=0)
    anomaly_count = db.Column(db.Integer, default=0)
    detection_method = db.Column(db.String(64), default="isolation_forest")
    threshold = db.Column(db.Float, default=0.5)
    transactions = db.relationship("Transaction", backref="dataset", lazy=True)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("dataset.id"), nullable=False)
    transaction_id = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    merchant_category = db.Column(db.String(128))
    location = db.Column(db.String(256))
    user_id = db.Column(db.String(128))
    is_anomaly = db.Column(db.Boolean, default=False)
    anomaly_score = db.Column(db.Float, default=0.0)
