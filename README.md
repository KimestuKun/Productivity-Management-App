# Productivity-Management-App (TaskFlow)

A structured productivity application that enables users to organise tasks, assign priorities, and monitor deadlines. By providing a clear overview of responsibilities, the system helps users improve time management and overall work efficiency.

---

## Running the app

### Prerequisites
- Python 3.10+
- Git

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd Productivity-Management-App
```

### 2. Create and activate a virtual environment

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the development server

```bash
python app.py
```

The app will be available at **http://127.0.0.1:5000**

---

## Seeding an admin account

Register a regular account through the app, then run:

```bash
python make_admin.py <your_username>
```

Restart the server after running the script. The **Admin** link will appear in the navbar when you log in.

---

## Admin features

| Route | Description |
|---|---|
| `/admin` | Dashboard with live-updating stats (refreshes every 5 s) |
| `/admin/users` | List all users; promote, demote, or delete |
| `/admin/logs` | System-wide activity log |
| `/admin/stats` | JSON endpoint polled by the dashboard |

---

## Project structure

```
app.py               — core Flask app and main routes (team)
database.py          — SQLite schema setup (team)
config.py            — app config (team)
routes_extra.py      — extra routes + admin panel (Isabella)
make_admin.py        — admin seeding script (Isabella)
Static/              — CSS and JS
Templates/           — Jinja2 templates
  admin/             — admin-only templates (Isabella)
```
