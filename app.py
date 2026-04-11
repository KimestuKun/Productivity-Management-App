# Had to import flask due to needing a communicator for the html pages
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from database import DBManager
from config import Config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db = DBManager()
db.usersTable()
db.taskTable()
db.userActivity()

# register user
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        db.cursor.execute(
            "INSERT INTO USERS (username, password_hash) VALUES (?, ?)",
            (username, hashed_password)
        )
        db.conn.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

# login user
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.cursor.execute(
            "SELECT * FROM USERS WHERE username=?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            db.cursor.execute(
                "INSERT INTO USERACTIVITY (user_id, action, timestamp) VALUES (?, ?, ?)",
                (user[0], "login", datetime.now())
            )
            db.conn.commit()
            return redirect(url_for("dashboard"))

    return render_template("login.html")

# dashboard
@app.route("/dashboard")

def dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))


    tasks = db.cursor.execute(

        "SELECT * FROM TASKS WHERE user_id=?",

        (session["user_id"],)

    ).fetchall()


    return render_template("dashboard.html", tasks=tasks)



# create task
@app.route("/create_task", methods=["POST"])

def create_task():
    title = request.form["title"]
    description = request.form["description"]
    priority = request.form["priority"]
    deadline = request.form["deadline"]
    db.cursor.execute("""
        INSERT INTO TASKS (title, description, priorityLevel, deadlineDate, user_id)
        VALUES (?, ?, ?, ?, ?)
    """,
    (title, description, priority, deadline, session["user_id"])
    )

    db.cursor.execute(
        "INSERT INTO USERACTIVITY (user_id, action, timestamp) VALUES (?, ?, ?)",
        (session["user_id"], "create task", datetime.now())
    )

    db.conn.commit()
    return redirect(url_for("dashboard"))



# delete task
@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):
    db.cursor.execute(
        "DELETE FROM TASKS WHERE task_id=?",
        (task_id,)
    )

    db.cursor.execute(
        "INSERT INTO USERACTIVITY (user_id, action, timestamp) VALUES (?, ?, ?)",
        (session["user_id"], "delete task", datetime.now())
    )

    db.conn.commit()
    return redirect(url_for("dashboard"))

# logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)