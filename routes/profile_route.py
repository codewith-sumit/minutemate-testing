from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from functools import wraps

profile_bp = Blueprint('profile', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Please log in to access this page.", "danger") # ❌ त्रुटि
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_email = session.get('user')
    user = User.query.filter_by(email=user_email).first()

    if not user:
        flash("User not found.", "danger") # ❌ त्रुटि
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        # Handle profile update
        name = request.form.get('name')
        email = request.form.get('email')

        # Handle password change
        current_password = request.form.get('current_password')
        print(request.form.get('current_password'))
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        # Update basic info
        if name and name != user.name:
            user.name = name
            session['name'] = name
            flash("Name updated successfully.", "success") # ✅ सफलता

        if email and email != user.email:
            if User.query.filter_by(email=email).first():
                flash("That email is already taken.", "danger") # ❌ त्रुटि
            else:
                user.email = email
                session['user'] = email
                flash("Email updated successfully.", "success") # ✅ सफलता
        
        db.session.commit()

        # Update password if fields are filled
        if current_password and new_password and confirm_new_password:
            if not check_password_hash(user.password_hash, current_password):
                flash("Current password is not correct.", "danger") # ❌ त्रुटि
            elif new_password != confirm_new_password:
                flash("New passwords do not match.", "danger") # ❌ त्रुटि
            else:
                user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash("Password updated successfully.", "success") # ✅ सफलता
        
        return redirect(url_for('profile.profile'))

    return render_template('profile.html', user=user, name=user.name, email=user.email)
