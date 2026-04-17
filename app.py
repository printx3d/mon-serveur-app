import tkinter as tk
from tkinter import messagebox
import requests

SERVER_URL = "https://mon-serveur-app.onrender.com"


# ---------------- LOGIN ----------------
def login():
    username = entry_user.get()
    password = entry_pass.get()

    response = requests.post(f"{SERVER_URL}/login", json={
        "username": username,
        "password": password
    })

    if response.status_code == 200:
        open_dashboard(username)
    else:
        messagebox.showerror("Erreur", "Identifiants incorrects")


def register():
    username = entry_user.get()
    password = entry_pass.get()

    response = requests.post(f"{SERVER_URL}/register", json={
        "username": username,
        "password": password
    })

    if response.status_code == 200:
        messagebox.showinfo("OK", "Compte créé")
    else:
        messagebox.showerror("Erreur", "Utilisateur existe déjà")


# ---------------- DASHBOARD ----------------
def open_dashboard(username):
    root.destroy()

    dash = tk.Tk()
    dash.title("Dashboard")
    dash.geometry("800x500")

    # HEADER
    header = tk.Frame(dash, bg="#1e1e2f", height=60)
    header.pack(fill="x")

    tk.Label(
        header,
        text=f"Bienvenue, {username}",
        fg="white",
        bg="#1e1e2f",
        font=("Arial", 14)
    ).pack(pady=15)

    # SIDEBAR
    sidebar = tk.Frame(dash, bg="#2b2b3d", width=200)
    sidebar.pack(side="left", fill="y")

    tk.Button(sidebar, text="📋 Tâches", width=20).pack(pady=10)
    tk.Button(sidebar, text="👥 Équipe", width=20).pack(pady=10)
    tk.Button(sidebar, text="⚙️ Paramètres", width=20).pack(pady=10)

    # MAIN AREA
    main = tk.Frame(dash, bg="#f5f5f5")
    main.pack(side="right", expand=True, fill="both")

    tk.Label(main, text="Dashboard", font=("Arial", 20)).pack(pady=20)

    tk.Label(main, text="👉 Ici tu ajouteras les tâches plus tard").pack()

    dash.mainloop()


# ---------------- LOGIN UI ----------------
root = tk.Tk()
root.title("Connexion")
root.geometry("300x200")

tk.Label(root, text="Utilisateur").pack()
entry_user = tk.Entry(root)
entry_user.pack()

tk.Label(root, text="Mot de passe").pack()
entry_pass = tk.Entry(root, show="*")
entry_pass.pack()

tk.Button(root, text="Se connecter", command=login).pack(pady=5)
tk.Button(root, text="Créer un compte", command=register).pack()

root.mainloop()
