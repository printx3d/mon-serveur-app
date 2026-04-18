from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app import db
from models import Task, Project, User, Notification

tasks_bp = Blueprint("tasks", __name__)

VALID_STATUSES = ("todo", "doing", "done")
VALID_PRIORITIES = ("low", "medium", "high")


@tasks_bp.route("/", methods=["GET"])
@jwt_required()
def list_tasks():
    """List tasks — optional filters: project_id, assignee_id, status, priority"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    query = Task.query

    # Filters
    project_id = request.args.get("project_id", type=int)
    assignee_id = request.args.get("assignee_id", type=int)
    status = request.args.get("status")
    priority = request.args.get("priority")
    mine = request.args.get("mine")  # ?mine=1 → only assigned to me

    if project_id:
        query = query.filter_by(project_id=project_id)
    if assignee_id:
        query = query.filter_by(assignee_id=assignee_id)
    if mine:
        query = query.filter_by(assignee_id=user_id)
    if status and status in VALID_STATUSES:
        query = query.filter_by(status=status)
    if priority and priority in VALID_PRIORITIES:
        query = query.filter_by(priority=priority)

    # Non-admin: only tasks from accessible projects
    if user.role != "admin":
        accessible_project_ids = [p.id for p in user.projects] + [p.id for p in user.owned_projects]
        query = query.filter(Task.project_id.in_(accessible_project_ids))

    tasks = query.order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks]), 200


@tasks_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict()), 200


@tasks_bp.route("/", methods=["POST"])
@jwt_required()
def create_task():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Task title is required"}), 400

    project_id = data.get("project_id")
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    project = Project.query.get_or_404(project_id)

    status = data.get("status", "todo")
    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {VALID_STATUSES}"}), 400

    priority = data.get("priority", "medium")
    if priority not in VALID_PRIORITIES:
        return jsonify({"error": f"priority must be one of {VALID_PRIORITIES}"}), 400

    deadline = None
    if data.get("deadline"):
        try:
            deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
        except ValueError:
            return jsonify({"error": "Invalid deadline format. Use ISO 8601."}), 400

    assignee_id = data.get("assignee_id")
    if assignee_id:
        User.query.get_or_404(assignee_id)

    task = Task(
        title=title,
        description=data.get("description", ""),
        status=status,
        priority=priority,
        deadline=deadline,
        project_id=project_id,
        assignee_id=assignee_id,
        creator_id=user_id,
    )
    db.session.add(task)
    db.session.flush()

    # Notify assignee
    if assignee_id and assignee_id != user_id:
        creator = User.query.get(user_id)
        notif = Notification(
            user_id=assignee_id,
            type="task_assigned",
            message=f"{creator.username} assigned you task «{title}» in {project.name}",
            related_task_id=task.id,
            related_project_id=project_id,
        )
        db.session.add(notif)

    db.session.commit()
    return jsonify(task.to_dict()), 201


@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    user_id = int(get_jwt_identity())
    task = Task.query.get_or_404(task_id)
    data = request.get_json()

    changed_fields = []

    if "title" in data and data["title"].strip():
        task.title = data["title"].strip()
        changed_fields.append("title")

    if "description" in data:
        task.description = data["description"]

    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return jsonify({"error": f"status must be one of {VALID_STATUSES}"}), 400
        task.status = data["status"]
        changed_fields.append("status")

    if "priority" in data:
        if data["priority"] not in VALID_PRIORITIES:
            return jsonify({"error": f"priority must be one of {VALID_PRIORITIES}"}), 400
        task.priority = data["priority"]
        changed_fields.append("priority")

    if "deadline" in data:
        if data["deadline"]:
            try:
                task.deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
            except ValueError:
                return jsonify({"error": "Invalid deadline format"}), 400
        else:
            task.deadline = None

    old_assignee_id = task.assignee_id
    if "assignee_id" in data:
        new_assignee_id = data["assignee_id"]
        if new_assignee_id:
            User.query.get_or_404(new_assignee_id)
        task.assignee_id = new_assignee_id
        changed_fields.append("assignee")

    task.updated_at = datetime.utcnow()
    db.session.flush()

    # Notifications
    editor = User.query.get(user_id)

    # New assignee notification
    if "assignee_id" in data and task.assignee_id and task.assignee_id != user_id:
        notif = Notification(
            user_id=task.assignee_id,
            type="task_assigned",
            message=f"{editor.username} assigned you task «{task.title}»",
            related_task_id=task.id,
            related_project_id=task.project_id,
        )
        db.session.add(notif)

    # Notify original assignee if task was modified (not reassigned)
    elif task.assignee_id and task.assignee_id != user_id and changed_fields:
        notif = Notification(
            user_id=task.assignee_id,
            type="task_updated",
            message=f"{editor.username} updated task «{task.title}» ({', '.join(changed_fields)})",
            related_task_id=task.id,
            related_project_id=task.project_id,
        )
        db.session.add(notif)

    db.session.commit()
    return jsonify(task.to_dict()), 200


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    user_id = int(get_jwt_identity())
    task = Task.query.get_or_404(task_id)

    user = User.query.get(user_id)
    if user.role != "admin" and task.creator_id != user_id and task.project.owner_id != user_id:
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"}), 200


@tasks_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    """Returns current user's task stats"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if user.role == "admin":
        all_tasks = Task.query.all()
    else:
        accessible_project_ids = [p.id for p in user.projects] + [p.id for p in user.owned_projects]
        all_tasks = Task.query.filter(Task.project_id.in_(accessible_project_ids)).all()

    my_tasks = [t for t in all_tasks if t.assignee_id == user_id]

    return jsonify({
        "my_tasks": {
            "total": len(my_tasks),
            "todo": [t.to_dict() for t in my_tasks if t.status == "todo"],
            "doing": [t.to_dict() for t in my_tasks if t.status == "doing"],
            "done": [t.to_dict() for t in my_tasks if t.status == "done"],
        },
        "team_stats": {
            "total": len(all_tasks),
            "todo": sum(1 for t in all_tasks if t.status == "todo"),
            "doing": sum(1 for t in all_tasks if t.status == "doing"),
            "done": sum(1 for t in all_tasks if t.status == "done"),
        }
    }), 200