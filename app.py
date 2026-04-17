import tkinter as tk
from tkinter import messagebox
import json
import os

FILE = "users.json"

# Créer le fichier s'il n'existe pas
if not os.path.exists(FILE):
    with open(FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(FILE, "w") as f:
        json.dump(users, f)

def login():
    username = entry_user.get()
    password = entry_pass.get()

    users = load_users()

    if username in users and users[username] == password:
        messagebox.showinfo("Succès", "Connexion réussie")
    else:
        messagebox.showerror("Erreur", "Identifiants incorrects")

def register():
    username = entry_user.get()
    password = entry_pass.get()

    users = load_users()

    if username in users:
        messagebox.showerror("Erreur", "Utilisateur déjà existant")
    else:
        users[username] = password
        save_users(users)
        messagebox.showinfo("Succès", "Compte créé")

# Interface
root = tk.Tk()
root.title("Connexion")
root.geometry("300x200")

tk.Label(root, text="Nom d'utilisateur").pack()
entry_user = tk.Entry(root)
entry_user.pack()

tk.Label(root, text="Mot de passe").pack()
entry_pass = tk.Entry(root, show="*")
entry_pass.pack()

tk.Button(root, text="Se connecter", command=login).pack(pady=5)
tk.Button(root, text="Créer un compte", command=register).pack()

root.mainloop()
