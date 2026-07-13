from . import db
from datetime import datetime, timezone

class Punishment(db.Model):
    __tablename__ = 'punishments'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    history = db.relationship('SpinHistory', backref='punishment', lazy=True, cascade="all, delete-orphan")

class SpinHistory(db.Model):
    __tablename__ = 'punishment_history'
    
    id = db.Column(db.Integer, primary_key=True)
    punishment_id = db.Column(db.Integer, db.ForeignKey('punishments.id', ondelete='SET NULL'), nullable=True)
    spun_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
