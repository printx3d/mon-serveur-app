"""
TeamFlow API Client
All HTTP calls to the backend are here — the rest of the app never calls requests directly.
"""
import requests
from typing import Optional, Dict, Any, List

# ── Change this to your Render URL in production ───────────────────────────────
API_BASE = "https://mon-serveur-app.onrender.com/api"
# For local dev: API_BASE = "http://localhost:5000/api"


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class TeamFlowAPI:
    def __init__(self):
        self.token: Optional[str] = None
        self.current_user: Optional[Dict] = None
        self.session = requests.Session()
        self.session.timeout = 10

        
    

    # ── Internal helpers ───────────────────────────────────────────────────────
    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _get(self, path: str, params: Dict = None) -> Any:
        try:
            r = self.session.get(f"{API_BASE}{path}", headers=self._headers(), params=params)
            if not r.ok:
                raise APIError(r.json().get("error", r.text), r.status_code)
            return r.json()
        except requests.exceptions.ConnectionError:
            raise APIError("Cannot connect to server. Check your internet connection.")
        except requests.exceptions.Timeout:
            raise APIError("Request timed out.")

    def _post(self, path: str, data: Dict = None) -> Any:
        try:
            r = self.session.post(f"{API_BASE}{path}", headers=self._headers(), json=data or {})
            print(f"STATUS: {r.status_code}")
            print(f"BODY: {r.text[:300]}")   # ← ajoute ça
            if not r.ok:
                raise APIError(r.json().get("error", r.text), r.status_code)
            return r.json()
        except requests.exceptions.ConnectionError:
            raise APIError("Cannot connect to server. Check your internet connection.")
        except requests.exceptions.Timeout:
            raise APIError("Request timed out.")

    def _put(self, path: str, data: Dict = None) -> Any:
        try:
            r = self.session.put(f"{API_BASE}{path}", headers=self._headers(), json=data or {})
            if not r.ok:
                raise APIError(r.json().get("error", r.text), r.status_code)
            return r.json()
        except requests.exceptions.ConnectionError:
            raise APIError("Cannot connect to server.")
        except requests.exceptions.Timeout:
            raise APIError("Request timed out.")

    def _delete(self, path: str) -> Any:
        try:
            r = self.session.delete(f"{API_BASE}{path}", headers=self._headers())
            if not r.ok:
                raise APIError(r.json().get("error", r.text), r.status_code)
            return r.json()
        except requests.exceptions.ConnectionError:
            raise APIError("Cannot connect to server.")
        except requests.exceptions.Timeout:
            raise APIError("Request timed out.")

    # ── Auth ───────────────────────────────────────────────────────────────────
    def register(self, username: str, email: str, password: str) -> Dict:
        data = self._post("/auth/register", {"username": username, "email": email, "password": password})
        self.token = data["access_token"]
        self.current_user = data["user"]
        return data

    def login(self, username: str, password: str) -> Dict:
        data = self._post("/auth/login", {"username": username, "password": password})
        self.token = data["access_token"]
        self.current_user = data["user"]
        return data

    def logout(self):
        try:
            self._post("/auth/logout")
        except APIError:
            pass
        self.token = None
        self.current_user = None

    def me(self) -> Dict:
        data = self._get("/auth/me")
        self.current_user = data
        return data

    # ── Users ──────────────────────────────────────────────────────────────────
    def get_users(self) -> List[Dict]:
        return self._get("/users/")

    def get_online_users(self) -> List[Dict]:
        return self._get("/users/online")

    def update_user(self, user_id: int, **kwargs) -> Dict:
        return self._put(f"/users/{user_id}", kwargs)

    def delete_user(self, user_id: int) -> Dict:
        return self._delete(f"/users/{user_id}")

    # ── Projects ───────────────────────────────────────────────────────────────
    def get_projects(self) -> List[Dict]:
        return self._get("/projects/")

    def get_project(self, project_id: int) -> Dict:
        return self._get(f"/projects/{project_id}")

    def create_project(self, name: str, description: str = "", color: str = "#6366f1") -> Dict:
        return self._post("/projects/", {"name": name, "description": description, "color": color})

    def update_project(self, project_id: int, **kwargs) -> Dict:
        return self._put(f"/projects/{project_id}", kwargs)

    def delete_project(self, project_id: int) -> Dict:
        return self._delete(f"/projects/{project_id}")

    def add_project_member(self, project_id: int, user_id: int) -> Dict:
        return self._post(f"/projects/{project_id}/members", {"user_id": user_id})

    def remove_project_member(self, project_id: int, user_id: int) -> Dict:
        return self._delete(f"/projects/{project_id}/members/{user_id}")

    def get_project_stats(self, project_id: int) -> Dict:
        return self._get(f"/projects/{project_id}/stats")

    # ── Tasks ──────────────────────────────────────────────────────────────────
    def get_tasks(self, project_id: int = None, assignee_id: int = None,
                  status: str = None, mine: bool = False) -> List[Dict]:
        params = {}
        if project_id:
            params["project_id"] = project_id
        if assignee_id:
            params["assignee_id"] = assignee_id
        if status:
            params["status"] = status
        if mine:
            params["mine"] = 1
        return self._get("/tasks/", params)

    def get_task(self, task_id: int) -> Dict:
        return self._get(f"/tasks/{task_id}")

    def create_task(self, title: str, project_id: int, description: str = "",
                    status: str = "todo", priority: str = "medium",
                    deadline: str = None, assignee_id: int = None) -> Dict:
        data = {
            "title": title, "project_id": project_id,
            "description": description, "status": status, "priority": priority,
        }
        if deadline:
            data["deadline"] = deadline
        if assignee_id:
            data["assignee_id"] = assignee_id
        return self._post("/tasks/", data)

    def update_task(self, task_id: int, **kwargs) -> Dict:
        return self._put(f"/tasks/{task_id}", kwargs)

    def delete_task(self, task_id: int) -> Dict:
        return self._delete(f"/tasks/{task_id}")

    def get_dashboard(self) -> Dict:
        return self._get("/tasks/dashboard")

    # ── Chat ───────────────────────────────────────────────────────────────────
    def get_messages(self, project_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        return self._get(f"/chat/{project_id}/messages", {"limit": limit, "offset": offset})

    def send_message(self, project_id: int, content: str) -> Dict:
        return self._post(f"/chat/{project_id}/messages", {"content": content})

    def delete_message(self, project_id: int, message_id: int) -> Dict:
        return self._delete(f"/chat/{project_id}/messages/{message_id}")

    # ── Notifications ──────────────────────────────────────────────────────────
    def get_notifications(self) -> List[Dict]:
        return self._get("/notifications/")

    def get_unread_count(self) -> int:
        return self._get("/notifications/unread-count").get("count", 0)

    def mark_notification_read(self, notif_id: int) -> Dict:
        return self._put(f"/notifications/{notif_id}/read")

    def mark_all_notifications_read(self) -> Dict:
        return self._put("/notifications/read-all")


# Singleton
api = TeamFlowAPI()