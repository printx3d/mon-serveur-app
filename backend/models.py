from app import db
from datetime import datetime


# ── Association table : project members ───────────────────────────────────────
project_members = db.Table(
    "project_members",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="member")  # admin / member
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_color = db.Column(db.String(7), default="#6366f1")  # hex color for avatar

    tasks_assigned = db.relationship("Task", foreign_keys="Task.assignee_id", backref="assignee", lazy=True)
    tasks_created = db.relationship("Task", foreign_keys="Task.creator_id", backref="creator", lazy=True)
    messages = db.relationship("Message", backref="sender", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)

    def to_dict(self, include_email=False):
        data = {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "is_online": self.is_online,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "avatar_color": self.avatar_color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data["email"] = self.email
        return data


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default="#6366f1")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship("User", backref="owned_projects")
    members = db.relationship("User", secondary=project_members, backref="projects")
    tasks = db.relationship("Task", backref="project", lazy=True, cascade="all, delete-orphan")
    messages = db.relationship("Message", backref="project", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_members=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "owner_id": self.owner_id,
            "owner": self.owner.to_dict() if self.owner else None,
            "task_count": len(self.tasks),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_members:
            data["members"] = [m.to_dict() for m in self.members]
        return data


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="todo")    # todo / doing / done
    priority = db.Column(db.String(10), default="medium")  # low / medium / high
    deadline = db.Column(db.DateTime)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "project_id": self.project_id,
            "project_name": self.project.name if self.project else None,
            "assignee": self.assignee.to_dict() if self.assignee else None,
            "creator": self.creator.to_dict() if self.creator else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "project_id": self.project_id,
            "sender": self.sender.to_dict() if self.sender else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(50))        # task_assigned / task_updated / project_invite
    message = db.Column(db.String(300))
    is_read = db.Column(db.Boolean, default=False)
    related_task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=True)
    related_project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "message": self.message,
            "is_read": self.is_read,
            "related_task_id": self.related_task_id,
            "related_project_id": self.related_project_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }