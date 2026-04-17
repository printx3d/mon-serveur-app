import tkinter as tk
from tkinter import messagebox
import requests

SERVER_URL = "https://mon-serveur-app.onrender.com"


# ---------------- LOGIN ----------------
def login():
    global username
    username = entry_user.get()
    password = entry_pass.get()

    r = requests.post(f"{SERVER_URL}/login", json={
        "username": username,
        "password": password
    })

    if r.status_code == 200:
        open_dashboard()
    else:
        messagebox.showerror("Erreur", "Login incorrect")


def register():
    r = requests.post(f"{SERVER_URL}/register", json={
        "username": entry_user.get(),
        "password": entry_pass.get()
    })

    if r.status_code == 200:
        messagebox.showinfo("OK", "Compte créé")
    else:
        messagebox.showerror("Erreur", "Utilisateur existe déjà")


# ---------------- DASHBOARD ----------------
def open_dashboard():
    root.destroy()

    dash = tk.Tk()
    dash.title("Dashboard")
    dash.geometry("800x500")

    # HEADER
    header = tk.Frame(dash, bg="#1e1e2f", height=60)
    header.pack(fill="x")

    tk.Label(header, text=f"Bienvenue {username}",
             fg="white", bg="#1e1e2f").pack(pady=15)

    # MAIN
    main = tk.Frame(dash)
    main.pack(fill="both", expand=True)

    # ENTRY TASK
    task_entry = tk.Entry(main, width=40)
    task_entry.pack(pady=10)

    # TASK LIST
    tasks_frame = tk.Frame(main)
    tasks_frame.pack()

    def load_tasks():
        for w in tasks_frame.winfo_children():
            w.destroy()

        r = requests.get(f"{SERVER_URL}/tasks/{username}")
        tasks = r.json()

        for t in tasks:
            tk.Label(tasks_frame, text=f"📌 {t[1]} ({t[2]})").pack()

    def add_task():
        requests.post(f"{SERVER_URL}/tasks/create", json={
            "title": task_entry.get(),
            "owner": username
        })
        load_tasks()

    tk.Button(main, text="Ajouter tâche", command=add_task).pack()

    load_tasks()

    dash.mainloop()


# ---------------- LOGIN UI ----------------
root = tk.Tk()
root.title("Login")
root.geometry("300x200")

tk.Label(root, text="User").pack()
entry_user = tk.Entry(root)
entry_user.pack()

tk.Label(root, text="Pass").pack()
entry_pass = tk.Entry(root, show="*")
entry_pass.pack()

tk.Button(root, text="Login", command=login).pack()
tk.Button(root, text="Register", command=register).pack()

root.mainloop()
