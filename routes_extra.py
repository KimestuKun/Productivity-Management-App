# routes_extra.py  — Isabella's custom routes (teammates: do not modify app.py)
#
# Contains:
#   - Context processor  (injects current_username + is_admin into every template)
#   - edit_task, update_status, activity  (original routes, unchanged)
#   - admin_required decorator
#   - /admin/*  routes (admin dashboard, user management, logs, stats API)

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from functools import wraps
from database import DBManager
from config import Config
from datetime import datetime, date

extra_bp = Blueprint('extra', __name__)

db = DBManager()

# ── One-time migration: add `role` column to USERS if it doesn't exist yet ──
# SQLite raises OperationalError when the column already exists, so we catch it.
try:
    db.cursor.execute("ALTER TABLE USERS ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
    db.conn.commit()
except Exception:
    pass  # column already present — safe to ignore


# ── Context processor ─────────────────────────────────────────────────────────
# Runs before every template render.
# Injects `current_username` and `is_admin` so base.html can show the Admin link
# without needing session['is_admin'] to be set at login time.
@extra_bp.app_context_processor
def inject_current_user():
    if 'user_id' in session:
        user = db.cursor.execute(
            "SELECT username, role FROM USERS WHERE user_id=?",
            (session['user_id'],)
        ).fetchone()
        if user:
            return {
                'current_username': user[0],
                'is_admin': user[1] == 'admin',
            }
    return {'current_username': None, 'is_admin': False}


# ── Admin guard decorator ─────────────────────────────────────────────────────
# Wrap any route with @admin_required to restrict it to admin users only.
# Non-admins are redirected to /dashboard with an error flash message.
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = db.cursor.execute(
            "SELECT role FROM USERS WHERE user_id=?",
            (session['user_id'],)
        ).fetchone()
        if not user or user[0] != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════════════════════════════
# ORIGINAL ROUTES (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

@extra_bp.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title       = request.form["title"]
        description = request.form.get("description", "")
        priority    = request.form["priority"]
        deadline    = request.form["deadline"]
        status      = request.form.get("status", "0")

        db.cursor.execute("""
            UPDATE TASKS
            SET title=?, description=?, priorityLevel=?, deadlineDate=?, completionStatus=?
            WHERE task_id=? AND user_id=?
        """, (title, description, priority, deadline, status, task_id, session["user_id"]))

        db.cursor.execute(
            "INSERT INTO USERACTIVITY (user_id, action, timestamp) VALUES (?, ?, ?)",
            (session["user_id"], "edit task", datetime.now())
        )
        db.conn.commit()
        return redirect(url_for("dashboard"))

    task = db.cursor.execute(
        "SELECT * FROM TASKS WHERE task_id=? AND user_id=?",
        (task_id, session["user_id"])
    ).fetchone()

    if not task:
        return redirect(url_for("dashboard"))

    return render_template("edit_task.html", task=task)


@extra_bp.route("/update_status/<int:task_id>", methods=["POST"])
def update_status(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    status = request.form.get("status", "0")

    db.cursor.execute(
        "UPDATE TASKS SET completionStatus=? WHERE task_id=? AND user_id=?",
        (status, task_id, session["user_id"])
    )

    status_labels = {"0": "set task pending", "1": "set task in progress", "2": "completed task"}
    action_label = status_labels.get(status, "update status")
    db.cursor.execute(
        "INSERT INTO USERACTIVITY (user_id, action, timestamp) VALUES (?, ?, ?)",
        (session["user_id"], action_label, datetime.now())
    )
    db.conn.commit()
    return redirect(url_for("dashboard"))


@extra_bp.route("/activity")
def activity():
    if "user_id" not in session:
        return redirect(url_for("login"))

    logs = db.cursor.execute(
        "SELECT action, timestamp FROM USERACTIVITY WHERE user_id=? ORDER BY timestamp DESC LIMIT 50",
        (session["user_id"],)
    ).fetchall()

    return render_template("activity.html", logs=logs)


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES  (all decorated with @admin_required)
# ═══════════════════════════════════════════════════════════════════════════════

@extra_bp.route("/admin")
@admin_required
def admin_dashboard():
    """Main admin dashboard — shows live stat cards that auto-refresh via JS."""
    # Pull headline numbers for the initial page load; JS refreshes them after.
    total_users     = db.cursor.execute("SELECT COUNT(*) FROM USERS").fetchone()[0]
    total_tasks     = db.cursor.execute("SELECT COUNT(*) FROM TASKS").fetchone()[0]
    completed_tasks = db.cursor.execute(
        "SELECT COUNT(*) FROM TASKS WHERE completionStatus=2"
    ).fetchone()[0]
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
    )


@extra_bp.route("/admin/users")
@admin_required
def admin_users():
    """List all registered users plus their task count and current role."""
    users = db.cursor.execute("""
        SELECT u.user_id, u.username, u.role,
               COUNT(t.task_id) AS task_count
        FROM USERS u
        LEFT JOIN TASKS t ON t.user_id = u.user_id
        GROUP BY u.user_id
        ORDER BY u.user_id
    """).fetchall()
    return render_template("admin/users.html", users=users)


@extra_bp.route("/admin/users/<int:user_id>/promote", methods=["POST"])
@admin_required
def admin_promote(user_id):
    """Promote a user to admin role."""
    db.cursor.execute(
        "UPDATE USERS SET role='admin' WHERE user_id=?", (user_id,)
    )
    db.cursor.execute(
        "INSERT INTO USERACTIVITY (user_id, action, timestamp) VALUES (?, ?, ?)",
        (session["user_id"], f"promoted user {user_id} to admin", datetime.now())
    )
    db.conn.commit()
    flash('User promoted to admin.', 'success')
    return redirect(url_for('extra.admin_users'))


@extra_bp.route("/admin/users/<int:user_id>/demote", methods=["POST"])
@admin_required
def admin_demote(user_id):
    """Demote an admin back to regular user role."""
    # Prevent an admin from locking themselves out
    if user_id == session["user_id"]:
        flash('You cannot demote yourself.', 'warning')
        return redirect(url_for('extra.admin_users'))
    db.cursor.execute(
        "UPDATE USERS SET role='user' WHERE user_id=?", (user_id,)
    )
    db.cursor.execute(
        "INSERT INTO USERACTIVITY (user_id, action, timestamp) VALUES (?, ?, ?)",
        (session["user_id"], f"demoted user {user_id} to user", datetime.now())
    )
    db.conn.commit()
    flash('User demoted to regular user.', 'success')
    return redirect(url_for('extra.admin_users'))


@extra_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    """Delete a user and all their tasks from the database."""
    # Prevent self-deletion
    if user_id == session["user_id"]:
        flash('You cannot delete your own account from the admin panel.', 'warning')
        return redirect(url_for('extra.admin_users'))
    db.cursor.execute("DELETE FROM TASKS WHERE user_id=?", (user_id,))
    db.cursor.execute("DELETE FROM USERACTIVITY WHERE user_id=?", (user_id,))
    db.cursor.execute("DELETE FROM USERS WHERE user_id=?", (user_id,))
    db.conn.commit()
    flash('User and all their data deleted.', 'success')
    return redirect(url_for('extra.admin_users'))


@extra_bp.route("/admin/logs")
@admin_required
def admin_logs():
    """View all system-wide activity logs, newest first."""
    logs = db.cursor.execute("""
        SELECT u.username, a.action, a.timestamp
        FROM USERACTIVITY a
        LEFT JOIN USERS u ON u.user_id = a.user_id
        ORDER BY a.timestamp DESC
        LIMIT 200
    """).fetchall()
    return render_template("admin/logs.html", logs=logs)


@extra_bp.route("/admin/stats")
@admin_required
def admin_stats():
    """
    JSON endpoint — polled every 5 s by the admin dashboard JS.
    Returns: total_users, total_tasks, completed_tasks, active_today.
    """
    today_str = date.today().isoformat()  # e.g. "2026-05-04"
    total_users = db.cursor.execute(
        "SELECT COUNT(*) FROM USERS"
    ).fetchone()[0]
    total_tasks = db.cursor.execute(
        "SELECT COUNT(*) FROM TASKS"
    ).fetchone()[0]
    completed_tasks = db.cursor.execute(
        "SELECT COUNT(*) FROM TASKS WHERE completionStatus=2"
    ).fetchone()[0]
    # Users who performed any action today
    active_today = db.cursor.execute(
        "SELECT COUNT(DISTINCT user_id) FROM USERACTIVITY WHERE timestamp LIKE ?",
        (today_str + '%',)
    ).fetchone()[0]
    return jsonify({
        "total_users":     total_users,
        "total_tasks":     total_tasks,
        "completed_tasks": completed_tasks,
        "active_today":    active_today,
    })
