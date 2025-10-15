from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from itsdangerous import SignatureExpired, BadSignature
from models import db, User
from flask_oauthlib.client import OAuth
# from routes import s, mail
from routes import s as serializer, mail

import os

auth_bp = Blueprint('auth', __name__)
oauth = OAuth()

# ✅ Google OAuth Setup
google = oauth.remote_app(
    'google',
    consumer_key=os.getenv("GOOGLE_CLIENT_ID"),
    consumer_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    request_token_params={'scope': 'email profile'},
    base_url='https://www.googleapis.com/oauth2/v1/',
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth'
)

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

# ----------------------------
# 🚪 Login 
# ----------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html", prefill_email=session.pop("prefill_email", None))

    form_type = request.form.get("form_type")

    # 🔐 Signup
    if form_type == "signup":
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if not all([name, email, password, confirm]):
            flash("All fields are required.", "danger")
            return redirect(url_for('auth.login'))
        elif password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('auth.login'))
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for('auth.login'))
        else:
            hashed = generate_password_hash(password)
            db.session.add(User(name=name, email=email, password_hash=hashed))
            db.session.commit()
            flash("Signup successful! Please log in.", "success")
            session["prefill_email"] = email
            return redirect(url_for('auth.login'))

    # 🔑 Login
    elif form_type == "login":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with this email.", "danger")
            return redirect(url_for('auth.login'))
        elif not check_password_hash(user.password_hash, password):
            flash("Incorrect password. Please try again.", "danger")
            return redirect(url_for('auth.login'))
        else:
            session['user'] = user.email
            session['role'] = user.role
            session['name'] = user.name
            flash("Logged in successfully!", "success")
            return redirect("/dashboard")



# ----------------------------
# 📝 Separate Signup Route
# ----------------------------
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if not all([name, email, password, confirm]):
            flash("All fields are required.", "danger")
            return redirect(url_for('auth.signup'))

        elif password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('auth.signup'))

        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for('auth.signup'))

        else:
            hashed = generate_password_hash(password)
            db.session.add(User(name=name, email=email, password_hash=hashed))
            db.session.commit()
            flash("Signup successful! Please log in.", "success")
            session["prefill_email"] = email
            return redirect(url_for('auth.login'))

    # GET request → show the signup page
    return render_template('signup.html')

        
        


        

# ----------------------------
# 🔗 Google Login
# ----------------------------
@auth_bp.route('/google_login')
def google_login():
    return google.authorize(callback=url_for('auth.google_callback', _external=True))

@auth_bp.route('/login/callback')
def google_callback():
    resp = google.authorized_response()
    if not resp or 'access_token' not in resp:
        flash("Google login failed.", "danger")
        return redirect('/login')

    session['google_token'] = (resp['access_token'], '')
    profile = google.get('userinfo').data
    email, name = profile['email'], profile.get('name', 'User')

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email, password_hash="", role="user")
        db.session.add(user)
        db.session.commit()

    session['user'] = user.email
    session['role'] = user.role
    session['name'] = user.name
    flash("Logged in via Google!", "success")
    return redirect("/dashboard")

# ----------------------------
# 🔐 Forget Password
# ----------------------------
@auth_bp.route('/forget', methods=['GET', 'POST'])
def forget():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with that email.", "danger")
        else:
            # token = s.dumps(email, salt='reset-password')
            token = serializer.s.dumps(email, salt='reset-password')
            link = url_for('auth.reset_token', token=token, _external=True)
            msg = Message("Reset your password", sender=os.getenv("EMAIL_USER"), recipients=[email])
            msg.body = f"Reset your password using this link:\n{link}"
            mail.send(msg)
            flash("A reset link has been sent to your email.", "success")
        return redirect('/login')

    return render_template("forget.html")

# ----------------------------
# 🔐 Reset Password
# ----------------------------
@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_token(token):
    try:
        email = s.loads(token, salt='reset-password', max_age=600)
    except SignatureExpired:
        flash("Reset link has expired. Please request again.", "danger")
        return redirect('/forget')
    except BadSignature:
        flash("Invalid or tampered reset link.", "danger")
        return redirect('/forget')

    if request.method == 'POST':
        new_pass = request.form['password']
        confirm = request.form['confirm']

        if new_pass != confirm:
            flash("Passwords do not match.", "danger")
        else:
            user = User.query.filter_by(email=email).first()
            user.password_hash = generate_password_hash(new_pass)
            db.session.commit()
            flash("Password updated successfully!", "success")
            return redirect('/login')

    return render_template("reset_password.html")

# ----------------------------
# 🚪 Logout
# ----------------------------
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')



















