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

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        owner TEXT,
        status TEXT DEFAULT 'todo'
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------- REGISTER ----------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data["username"]
    password = data["password"]

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, hashed))
        conn.commit()
        conn.close()
        return jsonify({"message": "OK"})
    except:
        return jsonify({"error": "exists"}), 400


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode(), user[0]):
        return jsonify({"message": "OK"})
    return jsonify({"error": "bad"}), 401


# ---------------- TASKS ----------------
@app.route("/tasks/create", methods=["POST"])
def create_task():
    data = request.json
    title = data["title"]
    owner = data["owner"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (title, owner) VALUES (?, ?)",
              (title, owner))
    conn.commit()
    conn.close()

    return jsonify({"message": "created"})


@app.route("/tasks/<username>")
def get_tasks(username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, title, status FROM tasks WHERE owner=?", (username,))
    tasks = c.fetchall()
    conn.close()

    return jsonify(tasks)


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
