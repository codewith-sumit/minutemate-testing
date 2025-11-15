from flask import Blueprint, render_template, redirect, session, flash
from models import User, Meeting
import json
from .decorators import login_required

dashboard_bp = Blueprint('dashboard', __name__)

# ----------------------------
#  Dashboard (User & Admin both see own meetings only)
# ----------------------------
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    user = User.query.filter_by(email=session['user']).first()

    if not user:
        flash("User not found.", "danger") 
        return redirect('/login')

    # Show only the logged-in user's meetings (even for admin)
    meetings = Meeting.query.filter_by(user_id=user.id).order_by(Meeting.created_at.desc()).all()

    # Convert stringified JSON to list
    for meeting in meetings:
        if isinstance(meeting.action_items, str):
            try:
                meeting.action_items = json.loads(meeting.action_items)
            except:
                meeting.action_items = []

    return render_template("dashboard.html", user=session['name'], user_email=session['user'] ,role=session['role'], meetings=meetings)

# ----------------------------
# Admin Page (user list only)
# ----------------------------
@dashboard_bp.route('/admin')
@login_required
def admin():
    if session.get('role') != 'admin':
        flash("Admins only.", "danger") 
        return redirect('/dashboard')

    users = User.query.all()
    return render_template("admin.html", users=users)

# ----------------------------
#  New Meeting Page
# ----------------------------
@dashboard_bp.route('/newmeet')
@login_required
def newmeet():
    return render_template("newmeet.html")

