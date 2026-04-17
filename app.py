import tkinter as tk
import requests

SERVER_URL = "https://mon-serveur-app.onrender.com"

username = ""


# ---------------- LOGIN ----------------
def login():
    global username
    username = entry_user.get()

    r = requests.post(f"{SERVER_URL}/login", json={
        "username": username,
        "password": entry_pass.get()
    })

    if r.status_code == 200:
        dashboard()
    else:
        print("error")


def register():
    requests.post(f"{SERVER_URL}/register", json={
        "username": entry_user.get(),
        "password": entry_pass.get()
    })


# ---------------- DASHBOARD ----------------
def dashboard():
    root.destroy()

    win = tk.Tk()
    win.geometry("900x600")
    win.title("Dashboard")

    # TASK INPUTS
    title = tk.Entry(win)
    title.pack()

    priority = tk.Entry(win)
    priority.pack()
    priority.insert(0, "low")

    deadline = tk.Entry(win)
    deadline.pack()
    deadline.insert(0, "2026-01-01")

    assigned = tk.Entry(win)
    assigned.pack()
    assigned.insert(0, username)

    frame = tk.Frame(win)
    frame.pack()

    def load():
        for w in frame.winfo_children():
            w.destroy()

        r = requests.get(f"{SERVER_URL}/tasks/{username}")
        for t in r.json():
            tk.Label(frame, text=t[1]).pack()

    def add():
        requests.post(f"{SERVER_URL}/tasks/create", json={
            "title": title.get(),
            "priority": priority.get(),
            "deadline": deadline.get(),
            "assigned_to": assigned.get(),
            "project_id": 1
        })
        load()

    tk.Button(win, text="Add Task", command=add).pack()

    load()

    win.mainloop()


# ---------------- LOGIN UI ----------------
root = tk.Tk()
root.geometry("300x200")

entry_user = tk.Entry(root)
entry_user.pack()

entry_pass = tk.Entry(root, show="*")
entry_pass.pack()

tk.Button(root, text="Login", command=login).pack()
tk.Button(root, text="Register", command=register).pack()

root.mainloop()
