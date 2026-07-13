from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Participant(db.Model):
    __tablename__ = 'participants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='Available') # Available, Assigned
    assigned_game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False) # Individual, Team
    team_size = db.Column(db.Integer, nullable=False, default=1)
    number_of_teams = db.Column(db.Integer, nullable=False, default=1)
    gender_rule = db.Column(db.String(50), nullable=False, default='Random')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    members = db.relationship('GameMember', backref='game', lazy=True, cascade="all, delete-orphan")
    participants = db.relationship('Participant', backref='game_assigned', lazy=True)

class GameMember(db.Model):
    __tablename__ = 'game_members'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=False)
    team_number = db.Column(db.Integer, nullable=False)
    
    participant = db.relationship('Participant', backref=db.backref('membership', uselist=False))

from .punishment import Punishment, SpinHistory
