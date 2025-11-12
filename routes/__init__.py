import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_oauthlib.client import OAuth
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Global extension instances
db = SQLAlchemy()
mail = Mail()
oauth = OAuth()
s = None  # Will initialize inside create_app

# Google OAuth client (will be assigned inside app context)
google = None

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY")

    # App config
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, '..', 'instance', 'minute_mate.db')
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

    # Init extensions
    db.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)

    global s
    s = URLSafeTimedSerializer(app.secret_key)

    # Recordings dir
    os.makedirs(os.path.join(app.root_path, '..', 'recordings'), exist_ok=True)

    # Gemini/Google Client can be initialized in modules

    # Register blueprints
    from .auth import auth_bp
    from .dashboard import dashboard_bp
    from .meeting_route import meeting_bp
    from .profile_route import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(meeting_bp)
    app.register_blueprint(profile_bp)

    # Optional root route
    @app.route('/')
    def home():
        return '', 204  # Can redirect to /login if needed

    return app
