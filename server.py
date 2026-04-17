from flask import Flask, request, jsonify
import sqlite3
import os
import bcrypt

app = Flask(__name__)
DB = "database.db"


# ---------------- INIT DB ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'member',
        online INTEGER DEFAULT 0
    )
    """)

    # PROJECTS
    c.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        owner TEXT
    )
    """)

    # TASKS
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        status TEXT,
        priority TEXT,
        deadline TEXT,
        assigned_to TEXT,
        project_id INTEGER
    )
    """)

    # CHAT
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        sender TEXT,
        message TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------- AUTH ----------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json

    hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())

    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (data["username"], hashed))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except:
        return jsonify({"error": "exists"}), 400


@app.route("/login", methods=["POST"])
def login():
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (data["username"],))
    user = c.fetchone()
    conn.close()

    if user and bcrypt.checkpw(data["password"].encode(), user[0]):
        return jsonify({"ok": True})

    return jsonify({"error": "bad"}), 401


# ---------------- PROJECTS ----------------
@app.route("/projects/create", methods=["POST"])
def create_project():
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO projects (name, owner) VALUES (?, ?)",
              (data["name"], data["owner"]))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/projects")
def get_projects():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM projects")
    data = c.fetchall()
    conn.close()
    return jsonify(data)


# ---------------- TASKS ----------------
@app.route("/tasks/create", methods=["POST"])
def create_task():
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    INSERT INTO tasks (title, status, priority, deadline, assigned_to, project_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["title"],
        "todo",
        data["priority"],
        data["deadline"],
        data["assigned_to"],
        data["project_id"]
    ))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/tasks/<user>")
def get_tasks(user):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE assigned_to=?", (user,))
    data = c.fetchall()
    conn.close()
    return jsonify(data)


@app.route("/tasks/delete", methods=["POST"])
def delete_task():
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (data["id"],))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/tasks/update", methods=["POST"])
def update_task():
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    UPDATE tasks
    SET title=?, status=?, priority=?, deadline=?, assigned_to=?
    WHERE id=?
    """, (
        data["title"],
        data["status"],
        data["priority"],
        data["deadline"],
        data["assigned_to"],
        data["id"]
    ))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


# ---------------- CHAT ----------------
@app.route("/chat/send", methods=["POST"])
def send():
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    INSERT INTO messages (project_id, sender, message, timestamp)
    VALUES (?, ?, ?, datetime('now'))
    """, (data["project_id"], data["sender"], data["message"]))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/chat/<int:project_id>")
def get_chat(project_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT sender, message FROM messages WHERE project_id=?",
              (project_id,))
    data = c.fetchall()
    conn.close()
    return jsonify(data)


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
