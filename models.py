from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    _password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # relationship to user's notes
    notes = db.relationship('Note', backref='user', cascade='all, delete-orphan', lazy=True)

    @validates('username')
    def validate_username(self, key, username):
        if not username or len(username.strip()) < 3:
            raise ValueError("Username must be at least 3 characters long")
        return username.strip()

    @hybrid_property
    def password_hash(self):
        return self._password_hash

    @password_hash.setter
    def password_hash(self, password):
        # hash password using bcrypt
        hashed = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = hashed.decode('utf-8')

    def authenticate(self, password):
        # verify password against stored hash
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # foreign key linking to the owner user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @validates('title')
    def validate_title(self, key, title):
        if not title or len(title.strip()) == 0:
            raise ValueError("Title is required")
        return title.strip()

    @validates('content')
    def validate_content(self, key, content):
        if not content or len(content.strip()) == 0:
            raise ValueError("Content is required")
        return content.strip()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id
        }

    def __repr__(self):
        return f'<Note {self.title}>'
