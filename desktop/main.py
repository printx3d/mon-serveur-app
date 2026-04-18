"""
TeamFlow Desktop — Main Application
Modern SaaS-style team management app built with customtkinter.
"""
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from typing import Optional, List, Dict

import customtkinter as ctk

from api_client import api, APIError

# ── Theme & Palette ────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Colors
C_BG        = "#0f1117"
C_SIDEBAR   = "#161b27"
C_CARD      = "#1e2535"
C_CARD2     = "#252d3d"
C_BORDER    = "#2a3348"
C_ACCENT    = "#6366f1"       # indigo
C_ACCENT2   = "#818cf8"
C_SUCCESS   = "#10b981"
C_WARN      = "#f59e0b"
C_DANGER    = "#ef4444"
C_TEXT      = "#e2e8f0"
C_MUTED     = "#64748b"
C_WHITE     = "#ffffff"

STATUS_COLORS = {"todo": C_MUTED, "doing": C_WARN, "done": C_SUCCESS}
STATUS_LABELS = {"todo": "📋 Todo", "doing": "⚡ Doing", "done": "✅ Done"}
PRIORITY_COLORS = {"low": C_SUCCESS, "medium": C_WARN, "high": C_DANGER}
PRIORITY_LABELS = {"low": "Low", "medium": "Medium", "high": "High"}

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_HEAD   = ("Segoe UI", 14, "bold")
FONT_SUB    = ("Segoe UI", 12, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 10)


# ══════════════════════════════════════════════════════════════════════════════
#  Helper widgets
# ══════════════════════════════════════════════════════════════════════════════

class Card(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=C_CARD, corner_radius=10,
                         border_width=1, border_color=C_BORDER, **kwargs)


class SectionTitle(ctk.CTkLabel):
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, text=text, font=FONT_HEAD,
                         text_color=C_TEXT, **kwargs)


class MutedLabel(ctk.CTkLabel):
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, text=text, font=FONT_SMALL,
                         text_color=C_MUTED, **kwargs)


class AccentButton(ctk.CTkButton):
    def __init__(self, parent, text, command=None, **kwargs):
        super().__init__(parent, text=text, command=command,
                         fg_color=C_ACCENT, hover_color=C_ACCENT2,
                         text_color=C_WHITE, font=FONT_BODY,
                         corner_radius=8, **kwargs)


class GhostButton(ctk.CTkButton):
    def __init__(self, parent, text, command=None, **kwargs):
        super().__init__(parent, text=text, command=command,
                         fg_color="transparent", hover_color=C_CARD2,
                         text_color=C_MUTED, font=FONT_BODY,
                         corner_radius=8, **kwargs)


def avatar_color(color: str, letter: str) -> ctk.CTkLabel:
    """Returns a small colored square label with the first letter"""
    lbl = ctk.CTkLabel(None, text=letter.upper(),
                       font=("Segoe UI", 12, "bold"),
                       text_color=C_WHITE, fg_color=color,
                       width=32, height=32, corner_radius=16)
    return lbl


def show_error(title: str, msg: str):
    messagebox.showerror(title, msg)


def show_info(title: str, msg: str):
    messagebox.showinfo(title, msg)


def run_async(fn, callback=None):
    """Run fn in a thread, then call callback(result) on the main thread."""
    def worker():
        try:
            result = fn()
            if callback:
                callback(result)
        except APIError as e:
            show_error("API Error", str(e))
        except Exception as e:
            show_error("Error", str(e))

    t = threading.Thread(target=worker, daemon=True)
    t.start()


# ══════════════════════════════════════════════════════════════════════════════
#  Auth Window
# ══════════════════════════════════════════════════════════════════════════════

class AuthWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TeamFlow — Sign In")
        self.geometry("440x600")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)
        self._mode = "login"  # login / register
        self._build()

    def _build(self):
        # Container
        frame = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=16,
                             border_width=1, border_color=C_BORDER)
        frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85)

        # Logo
        ctk.CTkLabel(frame, text="⬡ TeamFlow", font=("Segoe UI", 28, "bold"),
                     text_color=C_ACCENT).pack(pady=(36, 4))
        ctk.CTkLabel(frame, text="Collaborative workspace for your team",
                     font=FONT_SMALL, text_color=C_MUTED).pack(pady=(0, 28))

        # Tab bar
        tab_frame = ctk.CTkFrame(frame, fg_color=C_BG, corner_radius=8)
        tab_frame.pack(fill="x", padx=24, pady=(0, 20))

        self._login_tab = ctk.CTkButton(
            tab_frame, text="Sign In", command=lambda: self._switch_mode("login"),
            fg_color=C_ACCENT, hover_color=C_ACCENT2, text_color=C_WHITE,
            font=FONT_BODY, corner_radius=8, height=36
        )
        self._login_tab.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self._reg_tab = ctk.CTkButton(
            tab_frame, text="Register", command=lambda: self._switch_mode("register"),
            fg_color="transparent", hover_color=C_CARD2, text_color=C_MUTED,
            font=FONT_BODY, corner_radius=8, height=36
        )
        self._reg_tab.pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Form area
        self._form_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self._form_frame.pack(fill="x", padx=24, pady=(0, 24))

        self._build_form()

    def _switch_mode(self, mode: str):
        self._mode = mode
        if mode == "login":
            self._login_tab.configure(fg_color=C_ACCENT, text_color=C_WHITE)
            self._reg_tab.configure(fg_color="transparent", text_color=C_MUTED)
        else:
            self._reg_tab.configure(fg_color=C_ACCENT, text_color=C_WHITE)
            self._login_tab.configure(fg_color="transparent", text_color=C_MUTED)

        for w in self._form_frame.winfo_children():
            w.destroy()
        self._build_form()

    def _field(self, parent, label: str, placeholder: str, show: str = "") -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label, font=FONT_SMALL,
                     text_color=C_MUTED, anchor="w").pack(fill="x", pady=(8, 2))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, show=show,
                             fg_color=C_BG, border_color=C_BORDER,
                             text_color=C_TEXT, height=40, corner_radius=8)
        entry.pack(fill="x")
        return entry

    def _build_form(self):
        p = self._form_frame

        self._username = self._field(p, "Username", "your_username")
        if self._mode == "register":
            self._email = self._field(p, "Email", "you@example.com")
        self._password = self._field(p, "Password", "••••••••", show="•")

        btn_text = "Sign In" if self._mode == "login" else "Create Account"
        AccentButton(p, btn_text, command=self._submit, height=44).pack(fill="x", pady=(20, 0))

    def _submit(self):
        username = self._username.get().strip()
        password = self._password.get().strip()

        if not username or not password:
            show_error("Validation", "Please fill in all fields.")
            return

        def do_auth():
            if self._mode == "login":
                return api.login(username, password)
            else:
                email = self._email.get().strip()
                if not email:
                    raise APIError("Please enter your email.")
                return api.register(username, email, password)

        def on_success(data):
            self.destroy()
            app = MainApp()
            app.mainloop()

        run_async(do_auth, lambda data: self.after(0, lambda: on_success(data)))


# ══════════════════════════════════════════════════════════════════════════════
#  Main Application Window
# ══════════════════════════════════════════════════════════════════════════════

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TeamFlow")
        self.geometry("1280x800")
        self.minsize(1024, 600)
        self.configure(fg_color=C_BG)

        self.current_project: Optional[Dict] = None
        self.projects: List[Dict] = []
        self._notif_count = 0
        self._chat_poll_after = None

        self._build_layout()
        self._load_projects()
        self._show_dashboard()
        self._start_notification_poll()

    # ── Layout ─────────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, fg_color=C_SIDEBAR, corner_radius=0,
                                    border_width=0, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Main area
        self.main_frame = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        self.main_frame.pack(side="left", fill="both", expand=True)

        self._build_sidebar()

    def _build_sidebar(self):
        sb = self.sidebar

        # App logo
        logo_frame = ctk.CTkFrame(sb, fg_color="transparent", height=64)
        logo_frame.pack(fill="x", padx=16, pady=(16, 0))
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame, text="⬡ TeamFlow", font=("Segoe UI", 16, "bold"),
                     text_color=C_ACCENT).pack(side="left", pady=16)

        # User info
        user = api.current_user or {}
        uframe = ctk.CTkFrame(sb, fg_color=C_CARD, corner_radius=10,
                              border_width=1, border_color=C_BORDER)
        uframe.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(uframe, text=user.get("username", "User")[:18],
                     font=FONT_SUB, text_color=C_TEXT).pack(anchor="w", padx=12, pady=(10, 2))
        role = user.get("role", "member")
        role_color = C_ACCENT if role == "admin" else C_MUTED
        ctk.CTkLabel(uframe, text=f"● {role}", font=FONT_SMALL,
                     text_color=role_color).pack(anchor="w", padx=12, pady=(0, 10))

        # Nav divider
        ctk.CTkLabel(sb, text="WORKSPACE", font=("Segoe UI", 9, "bold"),
                     text_color=C_MUTED).pack(anchor="w", padx=16, pady=(8, 4))

        # Nav buttons
        nav_items = [
            ("🏠  Dashboard",   self._show_dashboard),
            ("✅  My Tasks",     self._show_my_tasks),
            ("👥  Team",         self._show_team),
            ("🔔  Notifications", self._show_notifications),
        ]
        self._nav_buttons = []
        for label, cmd in nav_items:
            btn = ctk.CTkButton(sb, text=label, command=cmd,
                                fg_color="transparent", hover_color=C_CARD2,
                                text_color=C_TEXT, font=FONT_BODY,
                                anchor="w", height=40, corner_radius=8)
            btn.pack(fill="x", padx=8, pady=1)
            self._nav_buttons.append(btn)

        # Notification badge placeholder
        self._notif_btn = self._nav_buttons[3]

        ctk.CTkLabel(sb, text="PROJECTS", font=("Segoe UI", 9, "bold"),
                     text_color=C_MUTED).pack(anchor="w", padx=16, pady=(16, 4))

        # Projects list
        self._project_list_frame = ctk.CTkScrollableFrame(sb, fg_color="transparent",
                                                           height=260)
        self._project_list_frame.pack(fill="x", padx=4)

        # New project
        AccentButton(sb, "+ New Project", command=self._open_new_project_dialog,
                     height=36).pack(fill="x", padx=12, pady=(8, 4))

        # Logout at bottom
        GhostButton(sb, "⎋  Sign Out", command=self._logout,
                    height=36).pack(fill="x", padx=12, pady=(4, 16), side="bottom")

    def _render_project_list(self):
        for w in self._project_list_frame.winfo_children():
            w.destroy()
        for project in self.projects:
            color = project.get("color", C_ACCENT)
            name = project.get("name", "Project")[:22]
            is_selected = (self.current_project and
                           self.current_project.get("id") == project.get("id"))
            btn = ctk.CTkButton(
                self._project_list_frame,
                text=f"● {name}",
                command=lambda p=project: self._open_project(p),
                fg_color=C_CARD if is_selected else "transparent",
                hover_color=C_CARD2,
                text_color=color if is_selected else C_TEXT,
                font=FONT_BODY, anchor="w", height=36, corner_radius=8
            )
            btn.pack(fill="x", padx=4, pady=1)

    # ── Navigation ─────────────────────────────────────────────────────────────
    def _clear_main(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

    def _page_header(self, title: str, subtitle: str = "") -> ctk.CTkFrame:
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=70)
        header.pack(fill="x", padx=28, pady=(24, 0))
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=title, font=FONT_TITLE, text_color=C_TEXT).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(header, text=subtitle, font=FONT_SMALL,
                         text_color=C_MUTED).pack(anchor="w")
        return header

    # ── Dashboard ──────────────────────────────────────────────────────────────
    def _show_dashboard(self):
        self._clear_main()
        user = api.current_user or {}
        self._page_header(f"Good day, {user.get('username', '')} 👋",
                          "Here's what's happening with your team today.")

        scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=12)

        # Stats row
        stats_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 16))

        def stat_card(parent, label, value, color):
            c = Card(parent)
            c.pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkLabel(c, text=str(value), font=("Segoe UI", 32, "bold"),
                         text_color=color).pack(padx=20, pady=(16, 0))
            ctk.CTkLabel(c, text=label, font=FONT_SMALL,
                         text_color=C_MUTED).pack(padx=20, pady=(0, 16))

        def load_dash():
            try:
                data = api.get_dashboard()
                self.after(0, lambda: self._fill_dashboard(scroll, stats_row, data, stat_card))
            except APIError as e:
                self.after(0, lambda: show_error("Dashboard", str(e)))

        # Show loading
        ctk.CTkLabel(stats_row, text="Loading...", font=FONT_BODY,
                     text_color=C_MUTED).pack(pady=16)
        threading.Thread(target=load_dash, daemon=True).start()

    def _fill_dashboard(self, scroll, stats_row, data, stat_card):
        for w in stats_row.winfo_children():
            w.destroy()

        my = data.get("my_tasks", {})
        team = data.get("team_stats", {})

        stat_card(stats_row, "My Todo", len(my.get("todo", [])), C_MUTED)
        stat_card(stats_row, "In Progress", len(my.get("doing", [])), C_WARN)
        stat_card(stats_row, "Completed", len(my.get("done", [])), C_SUCCESS)
        stat_card(stats_row, "Team Total", team.get("total", 0), C_ACCENT)

        # My Tasks columns
        cols_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cols_frame.pack(fill="both", expand=True, pady=8)

        for status in ("todo", "doing", "done"):
            tasks = my.get(status, [])
            col = ctk.CTkFrame(cols_frame, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True, padx=4)

            header = ctk.CTkFrame(col, fg_color=STATUS_COLORS[status],
                                  corner_radius=6, height=32)
            header.pack(fill="x", pady=(0, 8))
            header.pack_propagate(False)
            ctk.CTkLabel(header, text=f"{STATUS_LABELS[status]}  ({len(tasks)})",
                         font=FONT_SMALL, text_color=C_WHITE).pack(expand=True)

            for task in tasks[:8]:
                self._mini_task_card(col, task)

    def _mini_task_card(self, parent, task: Dict):
        card = Card(parent)
        card.pack(fill="x", pady=3)
        card.configure(fg_color=C_CARD2)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        title = task.get("title", "")[:40]
        ctk.CTkLabel(inner, text=title, font=FONT_BODY,
                     text_color=C_TEXT, anchor="w", wraplength=200).pack(anchor="w")

        meta = ctk.CTkFrame(inner, fg_color="transparent")
        meta.pack(fill="x", pady=(4, 0))

        prio = task.get("priority", "medium")
        ctk.CTkLabel(meta, text=f"● {PRIORITY_LABELS[prio]}", font=FONT_SMALL,
                     text_color=PRIORITY_COLORS[prio]).pack(side="left")

        proj = task.get("project_name", "")
        if proj:
            ctk.CTkLabel(meta, text=f"  {proj[:16]}", font=FONT_SMALL,
                         text_color=C_MUTED).pack(side="left")

        # Click to edit
        card.bind("<Button-1>", lambda e, t=task: self._open_task_dialog(t))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, t=task: self._open_task_dialog(t))

    # ── My Tasks ───────────────────────────────────────────────────────────────
    def _show_my_tasks(self):
        self._clear_main()
        self._page_header("My Tasks", "Tasks assigned to you across all projects")

        toolbar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        toolbar.pack(fill="x", padx=28, pady=(12, 0))

        self._tasks_status_filter = ctk.CTkOptionMenu(
            toolbar, values=["All", "todo", "doing", "done"],
            fg_color=C_CARD, button_color=C_ACCENT,
            text_color=C_TEXT, font=FONT_BODY, width=120,
            command=lambda v: self._load_my_tasks(container)
        )
        self._tasks_status_filter.pack(side="left", padx=(0, 8))

        AccentButton(toolbar, "+ New Task", command=self._open_new_task_dialog,
                     height=36, width=120).pack(side="right")

        container = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=8)

        self._load_my_tasks(container)

    def _load_my_tasks(self, container):
        for w in container.winfo_children():
            w.destroy()
        ctk.CTkLabel(container, text="Loading...", font=FONT_BODY,
                     text_color=C_MUTED).pack(pady=20)

        status_filter = self._tasks_status_filter.get()
        status = None if status_filter == "All" else status_filter

        def fetch():
            tasks = api.get_tasks(mine=True, status=status)
            self.after(0, lambda: self._render_task_list(container, tasks))

        threading.Thread(target=fetch, daemon=True).start()

    def _render_task_list(self, container, tasks: List[Dict]):
        for w in container.winfo_children():
            w.destroy()

        if not tasks:
            ctk.CTkLabel(container, text="No tasks found  ✓",
                         font=FONT_BODY, text_color=C_MUTED).pack(pady=40)
            return

        for task in tasks:
            self._task_row(container, task)

    def _task_row(self, parent, task: Dict):
        card = Card(parent)
        card.pack(fill="x", pady=4, padx=2)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)

        # Status dot
        status = task.get("status", "todo")
        ctk.CTkLabel(row, text="●", font=("Segoe UI", 18),
                     text_color=STATUS_COLORS[status], width=24).pack(side="left")

        # Title + description
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=12)

        ctk.CTkLabel(info, text=task.get("title", "")[:60],
                     font=FONT_SUB, text_color=C_TEXT, anchor="w").pack(anchor="w")

        desc = task.get("description", "")
        if desc:
            ctk.CTkLabel(info, text=desc[:80], font=FONT_SMALL,
                         text_color=C_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))

        # Meta
        meta = ctk.CTkFrame(row, fg_color="transparent")
        meta.pack(side="right")

        prio = task.get("priority", "medium")
        ctk.CTkLabel(meta, text=PRIORITY_LABELS[prio], font=FONT_SMALL,
                     text_color=PRIORITY_COLORS[prio]).pack(anchor="e")

        proj = task.get("project_name", "")
        if proj:
            ctk.CTkLabel(meta, text=proj[:18], font=FONT_SMALL,
                         text_color=C_MUTED).pack(anchor="e")

        dl = task.get("deadline")
        if dl:
            try:
                d = datetime.fromisoformat(dl.replace("Z", ""))
                overdue = d < datetime.utcnow()
                dl_text = d.strftime("%b %d")
                ctk.CTkLabel(meta, text=f"⏰ {dl_text}", font=FONT_SMALL,
                             text_color=C_DANGER if overdue else C_MUTED).pack(anchor="e")
            except Exception:
                pass

        # Click
        card.bind("<Button-1>", lambda e, t=task: self._open_task_dialog(t))
        for c in card.winfo_children():
            c.bind("<Button-1>", lambda e, t=task: self._open_task_dialog(t))

    # ── Project View ───────────────────────────────────────────────────────────
    def _open_project(self, project: Dict):
        self.current_project = project
        self._render_project_list()
        self._clear_main()

        # Header
        hdr = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=64)
        hdr.pack(fill="x", padx=28, pady=(20, 0))
        hdr.pack_propagate(False)

        color = project.get("color", C_ACCENT)
        ctk.CTkLabel(hdr, text="●", font=("Segoe UI", 24),
                     text_color=color).pack(side="left")
        ctk.CTkLabel(hdr, text=project.get("name", "Project"),
                     font=FONT_TITLE, text_color=C_TEXT).pack(side="left", padx=10)

        # Tabs
        tab_bar = ctk.CTkFrame(self.main_frame, fg_color=C_SIDEBAR,
                               corner_radius=10, height=44)
        tab_bar.pack(fill="x", padx=28, pady=12)
        tab_bar.pack_propagate(False)

        self._proj_content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self._proj_content.pack(fill="both", expand=True)

        tabs = [("📋 Tasks", self._show_project_tasks),
                ("💬 Chat",  self._show_project_chat),
                ("⚙ Settings", self._show_project_settings)]

        for label, cmd in tabs:
            ctk.CTkButton(tab_bar, text=label,
                          command=lambda c=cmd: self._switch_project_tab(c),
                          fg_color="transparent", hover_color=C_CARD2,
                          text_color=C_TEXT, font=FONT_BODY,
                          corner_radius=8, height=40).pack(side="left", padx=4, pady=4)

        self._show_project_tasks()

    def _switch_project_tab(self, cmd):
        for w in self._proj_content.winfo_children():
            w.destroy()
        cmd()

    def _show_project_tasks(self):
        content = self._proj_content
        for w in content.winfo_children():
            w.destroy()

        project = self.current_project
        if not project:
            return

        # Toolbar
        toolbar = ctk.CTkFrame(content, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(8, 4))

        AccentButton(toolbar, "+ New Task",
                     command=lambda: self._open_new_task_dialog(project_id=project["id"]),
                     height=36, width=130).pack(side="right")
        ctk.CTkLabel(toolbar, text=f"Project tasks — {project.get('task_count', 0)} total",
                     font=FONT_SMALL, text_color=C_MUTED).pack(side="left")

        # Kanban columns
        kanban = ctk.CTkFrame(content, fg_color="transparent")
        kanban.pack(fill="both", expand=True, padx=12, pady=4)

        self._kanban_cols = {}
        for status in ("todo", "doing", "done"):
            col = ctk.CTkFrame(kanban, fg_color=C_SIDEBAR,
                               corner_radius=10, border_width=1,
                               border_color=C_BORDER)
            col.pack(side="left", fill="both", expand=True, padx=6, pady=4)

            hdr = ctk.CTkFrame(col, fg_color="transparent", height=44)
            hdr.pack(fill="x", padx=12, pady=(12, 4))
            hdr.pack_propagate(False)

            ctk.CTkLabel(hdr, text=STATUS_LABELS[status], font=FONT_SUB,
                         text_color=STATUS_COLORS[status]).pack(side="left")

            scroll = ctk.CTkScrollableFrame(col, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=6, pady=4)
            self._kanban_cols[status] = scroll

        def load():
            tasks = api.get_tasks(project_id=project["id"])
            self.after(0, lambda: self._fill_kanban(tasks))

        threading.Thread(target=load, daemon=True).start()

    def _fill_kanban(self, tasks: List[Dict]):
        for status, col in self._kanban_cols.items():
            for w in col.winfo_children():
                w.destroy()
            col_tasks = [t for t in tasks if t.get("status") == status]

            if not col_tasks:
                ctk.CTkLabel(col, text="Empty", font=FONT_SMALL,
                             text_color=C_MUTED).pack(pady=20)
            for task in col_tasks:
                self._kanban_card(col, task)

    def _kanban_card(self, parent, task: Dict):
        card = Card(parent)
        card.pack(fill="x", pady=4)
        card.configure(fg_color=C_CARD2, cursor="hand2")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        # Priority strip
        prio = task.get("priority", "medium")
        strip = ctk.CTkFrame(inner, fg_color=PRIORITY_COLORS[prio],
                             width=3, corner_radius=2)
        strip.pack(side="left", fill="y", padx=(0, 10))

        body = ctk.CTkFrame(inner, fg_color="transparent")
        body.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(body, text=task.get("title", "")[:36], font=FONT_BODY,
                     text_color=C_TEXT, anchor="w", wraplength=160).pack(anchor="w")

        assignee = task.get("assignee")
        if assignee:
            ctk.CTkLabel(body, text=f"→ {assignee['username']}", font=FONT_SMALL,
                         text_color=C_MUTED).pack(anchor="w", pady=(4, 0))

        dl = task.get("deadline")
        if dl:
            try:
                d = datetime.fromisoformat(dl.replace("Z", ""))
                overdue = d < datetime.utcnow()
                ctk.CTkLabel(body, text=f"⏰ {d.strftime('%b %d')}",
                             font=FONT_SMALL,
                             text_color=C_DANGER if overdue else C_MUTED).pack(anchor="w")
            except Exception:
                pass

        card.bind("<Button-1>", lambda e, t=task: self._open_task_dialog(t))
        for c in card.winfo_children():
            c.bind("<Button-1>", lambda e, t=task: self._open_task_dialog(t))

    # ── Project Chat ───────────────────────────────────────────────────────────
    def _show_project_chat(self):
        content = self._proj_content
        project = self.current_project
        if not project:
            return

        # Messages area
        msg_frame = ctk.CTkScrollableFrame(content, fg_color="transparent")
        msg_frame.pack(fill="both", expand=True, padx=16, pady=(8, 0))

        # Input bar
        bar = ctk.CTkFrame(content, fg_color=C_CARD,
                           border_width=1, border_color=C_BORDER, corner_radius=12)
        bar.pack(fill="x", padx=16, pady=12)

        entry = ctk.CTkEntry(bar, placeholder_text="Type a message…",
                             fg_color="transparent", border_width=0,
                             text_color=C_TEXT, height=44, font=FONT_BODY)
        entry.pack(side="left", fill="x", expand=True, padx=12)

        def send():
            text = entry.get().strip()
            if not text:
                return
            entry.delete(0, "end")
            try:
                api.send_message(project["id"], text)
                self._load_messages(msg_frame, project["id"])
            except APIError as e:
                show_error("Chat", str(e))

        entry.bind("<Return>", lambda e: send())
        AccentButton(bar, "Send ↵", command=send,
                     height=36, width=90).pack(side="right", padx=8, pady=4)

        self._load_messages(msg_frame, project["id"])

        # Auto-refresh
        if self._chat_poll_after:
            self.after_cancel(self._chat_poll_after)

        def poll():
            self._load_messages(msg_frame, project["id"])
            self._chat_poll_after = self.after(5000, poll)

        self._chat_poll_after = self.after(5000, poll)

    def _load_messages(self, frame, project_id: int):
        def fetch():
            msgs = api.get_messages(project_id, limit=60)
            self.after(0, lambda: self._render_messages(frame, msgs))

        threading.Thread(target=fetch, daemon=True).start()

    def _render_messages(self, frame, messages: List[Dict]):
        # Preserve scroll position
        for w in frame.winfo_children():
            w.destroy()

        user_id = (api.current_user or {}).get("id")

        for msg in messages:
            is_me = msg.get("sender", {}).get("id") == user_id
            sender = msg.get("sender", {})

            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=3)

            if is_me:
                row.pack(fill="x", anchor="e")
                bubble = ctk.CTkFrame(row, fg_color=C_ACCENT, corner_radius=12)
                bubble.pack(side="right", padx=12)
                ctk.CTkLabel(bubble, text=msg.get("content", ""),
                             font=FONT_BODY, text_color=C_WHITE,
                             wraplength=320, justify="left").pack(padx=14, pady=(8, 4))
                ts = msg.get("created_at", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", ""))
                        ctk.CTkLabel(bubble, text=dt.strftime("%H:%M"),
                                     font=("Segoe UI", 9),
                                     text_color=C_ACCENT2).pack(padx=14, pady=(0, 6), anchor="e")
                    except Exception:
                        pass
            else:
                row.pack(fill="x", anchor="w")
                # Avatar
                color = sender.get("avatar_color", C_ACCENT)
                name = sender.get("username", "?")
                av = ctk.CTkLabel(row, text=name[0].upper(),
                                  font=("Segoe UI", 12, "bold"),
                                  text_color=C_WHITE, fg_color=color,
                                  width=32, height=32, corner_radius=16)
                av.pack(side="left", padx=(12, 8))

                right = ctk.CTkFrame(row, fg_color="transparent")
                right.pack(side="left")

                ctk.CTkLabel(right, text=name, font=FONT_SMALL,
                             text_color=C_MUTED).pack(anchor="w")
                bubble = ctk.CTkFrame(right, fg_color=C_CARD2, corner_radius=12)
                bubble.pack(anchor="w")
                ctk.CTkLabel(bubble, text=msg.get("content", ""),
                             font=FONT_BODY, text_color=C_TEXT,
                             wraplength=320, justify="left").pack(padx=14, pady=(8, 4))
                ts = msg.get("created_at", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", ""))
                        ctk.CTkLabel(bubble, text=dt.strftime("%H:%M"),
                                     font=("Segoe UI", 9),
                                     text_color=C_MUTED).pack(padx=14, pady=(0, 6), anchor="w")
                    except Exception:
                        pass

        # Scroll to bottom
        frame.after(50, lambda: frame._parent_canvas.yview_moveto(1.0))

    # ── Project Settings ───────────────────────────────────────────────────────
    def _show_project_settings(self):
        content = self._proj_content
        project = self.current_project
        if not project:
            return

        scroll = ctk.CTkScrollableFrame(content, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=12)

        SectionTitle(scroll, "Project Settings").pack(anchor="w", pady=(0, 16))

        # Edit form
        card = Card(scroll)
        card.pack(fill="x", pady=4)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(form, text="Project Name", font=FONT_SMALL,
                     text_color=C_MUTED).pack(anchor="w")
        name_entry = ctk.CTkEntry(form, fg_color=C_BG, text_color=C_TEXT,
                                  height=40, corner_radius=8)
        name_entry.insert(0, project.get("name", ""))
        name_entry.pack(fill="x", pady=(2, 12))

        ctk.CTkLabel(form, text="Description", font=FONT_SMALL,
                     text_color=C_MUTED).pack(anchor="w")
        desc_entry = ctk.CTkEntry(form, fg_color=C_BG, text_color=C_TEXT,
                                  height=40, corner_radius=8)
        desc_entry.insert(0, project.get("description", ""))
        desc_entry.pack(fill="x", pady=(2, 16))

        def save():
            try:
                api.update_project(project["id"],
                                   name=name_entry.get().strip(),
                                   description=desc_entry.get().strip())
                self._load_projects()
                show_info("Saved", "Project updated.")
            except APIError as e:
                show_error("Error", str(e))

        AccentButton(form, "Save Changes", command=save, height=40).pack(anchor="w")

        # Members section
        SectionTitle(scroll, "Members").pack(anchor="w", pady=(20, 8))
        members_card = Card(scroll)
        members_card.pack(fill="x", pady=4)

        self._render_members(members_card, project)

    def _render_members(self, parent, project: Dict):
        for w in parent.winfo_children():
            w.destroy()

        for m in project.get("members", []):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)

            color = m.get("avatar_color", C_ACCENT)
            av = ctk.CTkLabel(row, text=m["username"][0].upper(),
                              font=("Segoe UI", 11, "bold"),
                              text_color=C_WHITE, fg_color=color,
                              width=28, height=28, corner_radius=14)
            av.pack(side="left", padx=(0, 10))

            ctk.CTkLabel(row, text=m["username"], font=FONT_BODY,
                         text_color=C_TEXT).pack(side="left")

            if m["id"] != project["owner_id"]:
                def remove(uid=m["id"]):
                    try:
                        updated = api.remove_project_member(project["id"], uid)
                        self.current_project = updated
                        self._render_members(parent, updated)
                    except APIError as e:
                        show_error("Error", str(e))
                GhostButton(row, "Remove", command=remove,
                            height=28, width=80).pack(side="right")

        # Add member
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(4, 12))

        add_entry = ctk.CTkEntry(row, placeholder_text="Username to add…",
                                 fg_color=C_BG, text_color=C_TEXT,
                                 height=36, corner_radius=8)
        add_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def add_member():
            username = add_entry.get().strip()
            if not username:
                return
            try:
                users = api.get_users()
                user = next((u for u in users if u["username"].lower() == username.lower()), None)
                if not user:
                    show_error("Not Found", f"User «{username}» not found.")
                    return
                updated = api.add_project_member(project["id"], user["id"])
                self.current_project = updated
                self._render_members(parent, updated)
                add_entry.delete(0, "end")
            except APIError as e:
                show_error("Error", str(e))

        AccentButton(row, "Add", command=add_member,
                     height=36, width=70).pack(side="right")

    # ── Team ───────────────────────────────────────────────────────────────────
    def _show_team(self):
        self._clear_main()
        self._page_header("Team", "Your workspace members")

        scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=12)

        def load():
            users = api.get_users()
            self.after(0, lambda: self._render_team(scroll, users))

        threading.Thread(target=load, daemon=True).start()

    def _render_team(self, scroll, users: List[Dict]):
        for w in scroll.winfo_children():
            w.destroy()

        current_id = (api.current_user or {}).get("id")
        is_admin = (api.current_user or {}).get("role") == "admin"

        for user in users:
            card = Card(scroll)
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=12)

            # Avatar
            color = user.get("avatar_color", C_ACCENT)
            av = ctk.CTkLabel(row, text=user["username"][0].upper(),
                              font=("Segoe UI", 16, "bold"),
                              text_color=C_WHITE, fg_color=color,
                              width=44, height=44, corner_radius=22)
            av.pack(side="left", padx=(0, 14))

            # Info
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(info, text=user["username"], font=FONT_SUB,
                         text_color=C_TEXT).pack(anchor="w")

            role_color = C_ACCENT if user["role"] == "admin" else C_MUTED
            ctk.CTkLabel(info, text=f"● {user['role']}  {'🟢 Online' if user.get('is_online') else '⚫ Offline'}",
                         font=FONT_SMALL, text_color=role_color).pack(anchor="w")

            # Admin controls
            if is_admin and user["id"] != current_id:
                def promote(uid=user["id"], cur_role=user["role"]):
                    new_role = "member" if cur_role == "admin" else "admin"
                    try:
                        api.update_user(uid, role=new_role)
                        self._show_team()
                    except APIError as e:
                        show_error("Error", str(e))

                GhostButton(row, "Toggle Admin", command=promote,
                            height=32).pack(side="right", padx=4)

    # ── Notifications ──────────────────────────────────────────────────────────
    def _show_notifications(self):
        self._clear_main()
        self._page_header("Notifications")

        scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=8)

        AccentButton(self.main_frame, "Mark all as read",
                     command=lambda: self._mark_all_read(scroll),
                     height=36).pack(anchor="e", padx=28, pady=(0, 8))

        def load():
            notifs = api.get_notifications()
            self.after(0, lambda: self._render_notifs(scroll, notifs))

        threading.Thread(target=load, daemon=True).start()

    def _mark_all_read(self, scroll):
        try:
            api.mark_all_notifications_read()
            self._show_notifications()
            self._update_notif_badge(0)
        except APIError as e:
            show_error("Error", str(e))

    def _render_notifs(self, scroll, notifs: List[Dict]):
        for w in scroll.winfo_children():
            w.destroy()

        if not notifs:
            ctk.CTkLabel(scroll, text="All caught up! 🎉",
                         font=FONT_BODY, text_color=C_MUTED).pack(pady=40)
            return

        for n in notifs:
            is_read = n.get("is_read", False)
            card = Card(scroll)
            card.pack(fill="x", pady=3)
            if not is_read:
                card.configure(border_color=C_ACCENT)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=12)

            icon = {"task_assigned": "📌", "task_updated": "✏️",
                    "project_invite": "🎯"}.get(n.get("type", ""), "🔔")

            ctk.CTkLabel(row, text=icon, font=("Segoe UI", 20),
                         width=32).pack(side="left", padx=(0, 12))

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(inner, text=n.get("message", ""), font=FONT_BODY,
                         text_color=C_TEXT if not is_read else C_MUTED,
                         anchor="w", wraplength=500).pack(anchor="w")

            ts = n.get("created_at", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", ""))
                    ctk.CTkLabel(inner, text=dt.strftime("%b %d, %H:%M"),
                                 font=FONT_SMALL, text_color=C_MUTED).pack(anchor="w")
                except Exception:
                    pass

    # ── Task Dialog (Create / Edit) ────────────────────────────────────────────
    def _open_task_dialog(self, task: Dict = None, project_id: int = None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Task" if task else "New Task")
        dialog.geometry("520x600")
        dialog.configure(fg_color=C_BG)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        SectionTitle(scroll, "Edit Task" if task else "Create Task").pack(anchor="w", pady=(0, 16))

        def field(label, placeholder="", value=""):
            ctk.CTkLabel(scroll, text=label, font=FONT_SMALL,
                         text_color=C_MUTED).pack(anchor="w", pady=(8, 2))
            e = ctk.CTkEntry(scroll, placeholder_text=placeholder,
                             fg_color=C_CARD, text_color=C_TEXT,
                             height=40, corner_radius=8)
            if value:
                e.insert(0, value)
            e.pack(fill="x")
            return e

        title_e = field("Title *", "Task title", task.get("title", "") if task else "")

        ctk.CTkLabel(scroll, text="Description", font=FONT_SMALL,
                     text_color=C_MUTED).pack(anchor="w", pady=(8, 2))
        desc_e = ctk.CTkTextbox(scroll, fg_color=C_CARD, text_color=C_TEXT,
                                height=80, corner_radius=8)
        if task and task.get("description"):
            desc_e.insert("1.0", task["description"])
        desc_e.pack(fill="x")

        # Status & Priority
        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", pady=(12, 0))

        ctk.CTkLabel(row2, text="Status", font=FONT_SMALL,
                     text_color=C_MUTED).pack(anchor="w")
        status_var = ctk.CTkOptionMenu(row2, values=["todo", "doing", "done"],
                                       fg_color=C_CARD, button_color=C_ACCENT,
                                       text_color=C_TEXT, font=FONT_BODY)
        status_var.set(task.get("status", "todo") if task else "todo")
        status_var.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(row2, text="Priority", font=FONT_SMALL,
                     text_color=C_MUTED).pack(anchor="w")
        prio_var = ctk.CTkOptionMenu(row2, values=["low", "medium", "high"],
                                     fg_color=C_CARD, button_color=C_ACCENT,
                                     text_color=C_TEXT, font=FONT_BODY)
        prio_var.set(task.get("priority", "medium") if task else "medium")
        prio_var.pack(fill="x", pady=(2, 0))

        # Deadline
        deadline_e = field("Deadline (YYYY-MM-DD)", "2025-12-31",
                           (task["deadline"][:10] if task and task.get("deadline") else ""))

        # Assignee
        ctk.CTkLabel(scroll, text="Assignee", font=FONT_SMALL,
                     text_color=C_MUTED).pack(anchor="w", pady=(8, 2))
        users = []
        try:
            users = api.get_users()
        except APIError:
            pass

        user_names = ["(none)"] + [u["username"] for u in users]
        assignee_var = ctk.CTkOptionMenu(scroll, values=user_names,
                                         fg_color=C_CARD, button_color=C_ACCENT,
                                         text_color=C_TEXT, font=FONT_BODY)
        if task and task.get("assignee"):
            assignee_var.set(task["assignee"]["username"])
        else:
            assignee_var.set("(none)")
        assignee_var.pack(fill="x", pady=(2, 0))

        # Project selector (if not in a project context)
        projects = self.projects
        if not task and not project_id:
            ctk.CTkLabel(scroll, text="Project *", font=FONT_SMALL,
                         text_color=C_MUTED).pack(anchor="w", pady=(8, 2))
            proj_names = [p["name"] for p in projects]
            proj_var = ctk.CTkOptionMenu(scroll, values=proj_names if proj_names else ["No projects"],
                                          fg_color=C_CARD, button_color=C_ACCENT,
                                          text_color=C_TEXT, font=FONT_BODY)
            if self.current_project:
                proj_var.set(self.current_project["name"])
            proj_var.pack(fill="x", pady=(2, 0))
        else:
            proj_var = None

        # Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=(20, 0))

        def save():
            title = title_e.get().strip()
            if not title:
                show_error("Validation", "Title is required.")
                return

            # Resolve assignee
            assignee_name = assignee_var.get()
            assignee_id = None
            if assignee_name != "(none)":
                u = next((u for u in users if u["username"] == assignee_name), None)
                if u:
                    assignee_id = u["id"]

            # Resolve project
            pid = project_id or (self.current_project["id"] if self.current_project else None)
            if not pid and proj_var:
                proj_name = proj_var.get()
                p = next((p for p in projects if p["name"] == proj_name), None)
                if p:
                    pid = p["id"]

            if not pid:
                show_error("Validation", "Please select a project.")
                return

            dl = deadline_e.get().strip() or None
            if dl:
                dl = dl + "T00:00:00"

            desc = desc_e.get("1.0", "end-1c").strip()

            try:
                if task:
                    api.update_task(task["id"],
                                    title=title, description=desc,
                                    status=status_var.get(), priority=prio_var.get(),
                                    deadline=dl, assignee_id=assignee_id)
                else:
                    api.create_task(title, pid, desc,
                                    status_var.get(), prio_var.get(), dl, assignee_id)
                dialog.destroy()
                self._refresh_current_view()
            except APIError as e:
                show_error("Error", str(e))

        AccentButton(btn_row, "Save", command=save, height=42).pack(side="left", fill="x", expand=True, padx=(0, 4))

        if task:
            def delete_task():
                if messagebox.askyesno("Delete", f"Delete task «{task['title']}»?"):
                    try:
                        api.delete_task(task["id"])
                        dialog.destroy()
                        self._refresh_current_view()
                    except APIError as e:
                        show_error("Error", str(e))

            ctk.CTkButton(btn_row, text="Delete", command=delete_task,
                          fg_color=C_DANGER, hover_color="#dc2626",
                          text_color=C_WHITE, height=42, corner_radius=8).pack(side="right", padx=(4, 0))

    def _open_new_task_dialog(self, project_id: int = None):
        self._open_task_dialog(project_id=project_id)

    def _refresh_current_view(self):
        if self.current_project:
            self._show_project_tasks()
        else:
            self._show_my_tasks()

    # ── New Project Dialog ─────────────────────────────────────────────────────
    def _open_new_project_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Project")
        dialog.geometry("400x360")
        dialog.configure(fg_color=C_BG)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, fg_color=C_CARD, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        SectionTitle(frame, "Create Project").pack(pady=(20, 16), padx=20, anchor="w")

        ctk.CTkLabel(frame, text="Project Name *", font=FONT_SMALL,
                     text_color=C_MUTED).pack(anchor="w", padx=20)
        name_e = ctk.CTkEntry(frame, placeholder_text="My Awesome Project",
                              fg_color=C_BG, text_color=C_TEXT,
                              height=40, corner_radius=8)
        name_e.pack(fill="x", padx=20, pady=(2, 12))

        ctk.CTkLabel(frame, text="Description", font=FONT_SMALL,
                     text_color=C_MUTED).pack(anchor="w", padx=20)
        desc_e = ctk.CTkEntry(frame, placeholder_text="What is this project about?",
                              fg_color=C_BG, text_color=C_TEXT,
                              height=40, corner_radius=8)
        desc_e.pack(fill="x", padx=20, pady=(2, 12))

        ctk.CTkLabel(frame, text="Color", font=FONT_SMALL,
                     text_color=C_MUTED).pack(anchor="w", padx=20)
        colors = ["#6366f1", "#ec4899", "#14b8a6", "#f59e0b", "#ef4444", "#8b5cf6"]
        color_var = tk.StringVar(value=colors[0])
        cframe = ctk.CTkFrame(frame, fg_color="transparent")
        cframe.pack(anchor="w", padx=20, pady=(2, 16))
        for c in colors:
            btn = ctk.CTkButton(cframe, text="", width=28, height=28,
                                fg_color=c, hover_color=c, corner_radius=14,
                                command=lambda col=c: color_var.set(col))
            btn.pack(side="left", padx=3)

        def create():
            name = name_e.get().strip()
            if not name:
                show_error("Validation", "Project name is required.")
                return
            try:
                project = api.create_project(name, desc_e.get().strip(), color_var.get())
                self.projects.append(project)
                self._render_project_list()
                dialog.destroy()
                self._open_project(project)
            except APIError as e:
                show_error("Error", str(e))

        AccentButton(frame, "Create Project", command=create,
                     height=44).pack(fill="x", padx=20, pady=(0, 20))

    # ── Data Loading ───────────────────────────────────────────────────────────
    def _load_projects(self):
        def fetch():
            try:
                projects = api.get_projects()
                self.projects = projects
                self.after(0, self._render_project_list)
            except APIError:
                pass

        threading.Thread(target=fetch, daemon=True).start()

    # ── Notification polling ───────────────────────────────────────────────────
    def _start_notification_poll(self):
        def poll():
            try:
                count = api.get_unread_count()
                self.after(0, lambda: self._update_notif_badge(count))
            except APIError:
                pass
            self.after(30000, poll)  # every 30s

        self.after(2000, poll)

    def _update_notif_badge(self, count: int):
        self._notif_count = count
        label = f"🔔  Notifications{f'  ({count})' if count else ''}"
        if hasattr(self, "_notif_btn"):
            self._notif_btn.configure(
                text=label,
                text_color=C_WARN if count else C_TEXT
            )

    # ── Logout ─────────────────────────────────────────────────────────────────
    def _logout(self):
        api.logout()
        self.destroy()
        auth = AuthWindow()
        auth.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # Try to restore session
    auth_win = AuthWindow()
    auth_win.mainloop()


if __name__ == "__main__":
    main()