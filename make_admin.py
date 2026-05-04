# make_admin.py — Isabella's admin seeding script
#
# Usage:
#   python make_admin.py <username>
#
# Flips the named user's role to 'admin' in the database.
# Run this once after registering your demo account so you can show
# the admin panel without modifying the database manually.

import sys
import sqlite3
from config import Config


def make_admin(username: str) -> None:
    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()

    # Make sure the role column exists (safe if already present)
    try:
        cursor.execute("ALTER TABLE USERS ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists

    # Look up the user
    row = cursor.execute(
        "SELECT user_id, role FROM USERS WHERE username=?", (username,)
    ).fetchone()

    if not row:
        print(f"[ERROR] No user found with username '{username}'.")
        print("        Registered usernames in the database:")
        for (u,) in cursor.execute("SELECT username FROM USERS").fetchall():
            print(f"          - {u}")
        conn.close()
        sys.exit(1)

    user_id, current_role = row
    if current_role == 'admin':
        print(f"[INFO]  '{username}' is already an admin. Nothing changed.")
    else:
        cursor.execute("UPDATE USERS SET role='admin' WHERE user_id=?", (user_id,))
        conn.commit()
        print(f"[OK]    '{username}' (user_id={user_id}) has been promoted to admin.")
        print("        Restart the Flask server, then log in to see the Admin link.")

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <username>")
        sys.exit(1)
    make_admin(sys.argv[1])
