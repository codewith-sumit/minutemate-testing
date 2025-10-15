# create_db.py

from routes import app, db

# Create all tables defined in models
with app.app_context():
    db.create_all()
    print("✅ Tables created successfully in minute_mate.db")
#minute_mate