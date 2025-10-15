from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

# ---------------------------
# User Table
# ---------------------------
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')  # user or admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    meetings = db.relationship('Meeting', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"

# ---------------------------
# Meeting Table
# ---------------------------
class Meeting(db.Model):
    __tablename__ = 'meetings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # ✅ changed from audio_file to filename
    transcript = db.Column(db.Text)
    summary = db.Column(db.Text)
    action_items = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Meeting {self.title}>"

# ---------------------------
# Optional: Create default admin user
# ---------------------------
def create_admin(app):
    with app.app_context():
        admin_email = "sumit@admin.com"
        existing = User.query.filter_by(email=admin_email).first()
        if not existing:
            admin = User(
                name="Sumit",
                email=admin_email,
                password_hash=generate_password_hash("1234"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created.")
        else:
            print("ℹ️ Admin user already exists.")




