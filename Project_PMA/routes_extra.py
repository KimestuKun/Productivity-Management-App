"""
routes_extra.py — Additional routes added by [your name] (frontend/completion work)

This file adds two routes that are missing from the teammates' app.py:
  - GET/POST  /edit_task/<task_id>   (edit task form + save)
  - GET       /activity              (activity log page)

HOW TO ACTIVATE (add these 2 lines to app.py, after `app = Flask(__name__)`):
  ─────────────────────────────────────────────
  from routes_extra import extra_bp
  app.register_blueprint(extra_bp)
  ─────────────────────────────────────────────
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from database import DBManager
from config import Config
from datetime import datetime

# Register as a Blueprint so it plugs into the existing app without modifying app.py logic
extra_bp = Blueprint('extra', __name__)

# Separate db connection for this module (teammates' db object lives in app.py scope)
db = DBManager()


# ── App-wide Context Processor ────────────────────────────────────────────────
# @extra_bp.app_context_processor injects variables into ALL templates in the app,
# including dashboard.html which is rendered by the teammates' app.py route.
# This is the only way to pass `current_username` to that template without
# touching app.py. It runs on every request after the blueprint is registered.
@extra_bp.app_context_processor
def inject_current_user():
    """Make current_username available in every template, app-wide."""
    if 'user_id' in session:
        # Reusing DBManager — same class and connection approach as teammates' app.py
        user = db.cursor.execute(
            "SELECT username FROM USERS WHERE user_id=?",
            (session['user_id'],)
        ).fetchone()
        return {'current_username': user[0] if user else None}
    return {'current_username': None}


# ── Edit Task ──────────────────────────────────────────────────────────────────
@extra_bp.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    """Load a task for editing (GET) or save the updated values (POST)."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title       = request.form["title"]
        description = request.form.get("description", "")
        priority    = request.form["priority"]
        deadline    = request.form["deadline"]
        status      = request.form.get("status", "0")   # 0=Pending 1=InProgress 2=Completed

        # Update only rows belonging to this user (security: user_id check)
        db.cursor.execute("""
            UPDATE TASKS
            SET title=?, description=?, priorityLevel=?, deadlineDate=?, completionStatus=?
            WHERE task_id=? AND user_id=?
        """, (title, description, priority, deadline, status, task_id, session["user_id"]))

        # Log the activity
        db.cursor.execute(
            "INSERT INTO USERACTIVITY (user_id, action, timestamp) VALUES (?, ?, ?)",
            (session["user_id"], "edit task", datetime.now())
        )
        db.conn.commit()
        return redirect(url_for("dashboard"))

    # GET: fetch the task (only if it belongs to the logged-in user)
    task = db.cursor.execute(
        "SELECT * FROM TASKS WHERE task_id=? AND user_id=?",
        (task_id, session["user_id"])
    ).fetchone()

    if not task:
        # Task not found or belongs to another user — redirect silently
        return redirect(url_for("dashboard"))

    return render_template("edit_task.html", task=task)


# ── Update Task Status (quick-change from dashboard) ──────────────────────────
@extra_bp.route("/update_status/<int:task_id>", methods=["POST"])
def update_status(task_id):
    """Quick-update completionStatus from the dashboard status dropdown."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    status = request.form.get("status", "0")

    # Security: AND user_id=? ensures users can only update their own tasks
    db.cursor.execute(
        "UPDATE TASKS SET completionStatus=? WHERE task_id=? AND user_id=?",
        (status, task_id, session["user_id"])
    )

    # Log the action (same INSERT pattern as teammates' app.py)
    status_labels = {"0": "set task pending", "1": "set task in progress", "2": "completed task"}
    action_label = status_labels.get(status, "update status")
    db.cursor.execute(
        "INSERT INTO USERACTIVITY (user_id, action, timestamp) VALUES (?, ?, ?)",
        (session["user_id"], action_label, datetime.now())
    )
    db.conn.commit()
    return redirect(url_for("dashboard"))


# ── Activity Log ───────────────────────────────────────────────────────────────
@extra_bp.route("/activity")
def activity():
    """Display the 50 most recent actions for the logged-in user."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Order by timestamp DESC so newest actions appear first
    logs = db.cursor.execute(
        "SELECT action, timestamp FROM USERACTIVITY WHERE user_id=? ORDER BY timestamp DESC LIMIT 50",
        (session["user_id"],)
    ).fetchall()

    return render_template("activity.html", logs=logs)
