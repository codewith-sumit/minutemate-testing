from flask import Blueprint, render_template, redirect, session, flash
from models import User, Meeting
import json

dashboard_bp = Blueprint('dashboard', __name__)

# ----------------------------
# 🧾 Dashboard (User & Admin both see own meetings only)
# ----------------------------
@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please log in first!", "warning") # ⚠️ चेतावनी
        return redirect('/login')

    user = User.query.filter_by(email=session['user']).first()

    if not user:
        flash("User not found.", "danger") # ❌ त्रुटि
        return redirect('/login')

    # ✅ Show only the logged-in user's meetings (even for admin)
    meetings = Meeting.query.filter_by(user_id=user.id).order_by(Meeting.created_at.desc()).all()

    # ✅ Convert stringified JSON to list
    for meeting in meetings:
        if isinstance(meeting.action_items, str):
            try:
                meeting.action_items = json.loads(meeting.action_items)
            except:
                meeting.action_items = []

    return render_template("dashboard.html", user=session['name'], user_email=session['user'] ,role=session['role'], meetings=meetings)

# ----------------------------
# 👑 Admin Page (user list only)
# ----------------------------
@dashboard_bp.route('/admin')
def admin():
    if session.get('role') != 'admin':
        flash("Admins only.", "danger") # ❌ त्रुटि
        return redirect('/dashboard')

    users = User.query.all()
    return render_template("admin.html", users=users)

# ----------------------------
# ➕ New Meeting Page
# ----------------------------
@dashboard_bp.route('/newmeet')


def newmeet():
    return render_template("newmeet.html")






























# from flask import Blueprint, render_template, redirect, session, flash
# from models import User, Meeting  # ✅ import directly from models.py
# import json

# dashboard_bp = Blueprint('dashboard', __name__)

# # ----------------------------
# # 🧾 Dashboard (User & Admin)
# # ----------------------------
# @dashboard_bp.route('/dashboard')
# def dashboard():
#     if 'user' not in session:
#         flash("Please log in first!", "warning")
#         return redirect('/login')

#     user = User.query.filter_by(email=session['user']).first()

#     if not user:
#         flash("User not found.", "danger")
#         return redirect('/login')

#     meetings = Meeting.query.order_by(Meeting.created_at.desc()).all() if session.get('role') == 'admin' else \
#                Meeting.query.filter_by(user_id=user.id).order_by(Meeting.created_at.desc()).all()

#     # ✅ Convert stringified JSON to list
#     for meeting in meetings:

#         if isinstance(meeting.action_items, str):
#             try:
#                 meeting.action_items = json.loads(meeting.action_items)
#             except:
#                 meeting.action_items = []

#     return render_template("dashboard.html", user=session['name'], role=session['role'], meetings=meetings)

# # ----------------------------
# # 👑 Admin Page
# # ----------------------------
# @dashboard_bp.route('/admin')
# def admin():
#     if session.get('role') != 'admin':
#         flash("Admins only.", "danger")
#         return redirect('/dashboard')

#     users = User.query.all()
#     return render_template("admin.html", users=users)

# # ----------------------------
# # ➕ New Meeting Page
# # ----------------------------
# @dashboard_bp.route('/newmeet')
# def newmeet():
#     return render_template("newmeet.html")
