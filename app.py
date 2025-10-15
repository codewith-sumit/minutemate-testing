import os
from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_oauthlib.client import OAuth
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

from models import db  # ✅ db imported from models.py

# --- Load environment variables ---
load_dotenv()

# --- Global Extensions ---
mail = Mail()
oauth = OAuth()
s = None  # Serializer will be initialized in create_app()

# --- Flask App Factory ---
def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY")

    # --- Config ---
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'minute_mate.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv('EMAIL_USER'),
        MAIL_PASSWORD=os.getenv('EMAIL_PASS'),
    )

    # --- Initialize Extensions ---
    db.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)

    # global s
    s = URLSafeTimedSerializer(app.secret_key)

    # --- Ensure directories exist ---
    os.makedirs(os.path.join(basedir, 'recordings'), exist_ok=True)
    os.makedirs(os.path.join(basedir, 'fonts'), exist_ok=True)

    # --- Register Blueprints ---
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.meeting_route import meeting_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(meeting_bp)

    # --- Default Route ---
    @app.route('/')
    def home():
        return redirect('/login')

    return app

# --- Run App ---
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        from models import create_admin
        create_admin(app)
    app.run(debug=True)
