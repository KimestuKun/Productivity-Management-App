import sqlite3
from config import Config


class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def usersTable(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS USERS (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """)
        self.conn.commit()

    def taskTable(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS TASKS (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priorityLevel INTEGER,
            deadlineDate TEXT,
            completionStatus INTEGER DEFAULT 0,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES USERS(user_id)
        )
        """)
        self.conn.commit()

    def userActivity(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS USERACTIVITY(
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES USERS(user_id)
        )
        """)
        self.conn.commit()
