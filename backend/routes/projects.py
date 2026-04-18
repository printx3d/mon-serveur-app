from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models import Project, User, Notification

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("/", methods=["GET"])
@jwt_required()
def list_projects():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if user.role == "admin":
        projects = Project.query.order_by(Project.updated_at.desc()).all()
    else:
        # Member: only projects they own or are member of
        projects = Project.query.filter(
            (Project.owner_id == user_id) | (Project.members.any(id=user_id))
        ).order_by(Project.updated_at.desc()).all()

    return jsonify([p.to_dict(include_members=True) for p in projects]), 200


@projects_bp.route("/<int:project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)

    if not _can_access(user_id, project):
        return jsonify({"error": "Forbidden"}), 403

    return jsonify(project.to_dict(include_members=True)), 200


@projects_bp.route("/", methods=["POST"])
@jwt_required()
def create_project():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Project name is required"}), 400

    project = Project(
        name=name,
        description=data.get("description", ""),
        color=data.get("color", "#6366f1"),
        owner_id=user_id,
    )
    # Owner is also a member
    owner = User.query.get(user_id)
    project.members.append(owner)

    db.session.add(project)
    db.session.commit()

    return jsonify(project.to_dict(include_members=True)), 201


@projects_bp.route("/<int:project_id>", methods=["PUT"])
@jwt_required()
def update_project(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)

    if not _can_manage(user_id, project):
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    if "name" in data and data["name"].strip():
        project.name = data["name"].strip()
    if "description" in data:
        project.description = data["description"]
    if "color" in data:
        project.color = data["color"]

    db.session.commit()
    return jsonify(project.to_dict(include_members=True)), 200


@projects_bp.route("/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)

    if not _can_manage(user_id, project):
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted"}), 200


@projects_bp.route("/<int:project_id>/members", methods=["POST"])
@jwt_required()
def add_member(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)

    if not _can_manage(user_id, project):
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    target_user_id = data.get("user_id")
    if not target_user_id:
        return jsonify({"error": "user_id required"}), 400

    target = User.query.get_or_404(target_user_id)
    if target not in project.members:
        project.members.append(target)

        # Notify the added user
        notif = Notification(
            user_id=target.id,
            type="project_invite",
            message=f"You were added to project «{project.name}»",
            related_project_id=project.id,
        )
        db.session.add(notif)
        db.session.commit()

    return jsonify(project.to_dict(include_members=True)), 200


@projects_bp.route("/<int:project_id>/members/<int:target_user_id>", methods=["DELETE"])
@jwt_required()
def remove_member(project_id, target_user_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)

    if not _can_manage(user_id, project):
        return jsonify({"error": "Forbidden"}), 403

    target = User.query.get_or_404(target_user_id)
    if target == project.owner:
        return jsonify({"error": "Cannot remove project owner"}), 400

    if target in project.members:
        project.members.remove(target)
        db.session.commit()

    return jsonify(project.to_dict(include_members=True)), 200


@projects_bp.route("/<int:project_id>/stats", methods=["GET"])
@jwt_required()
def project_stats(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)

    if not _can_access(user_id, project):
        return jsonify({"error": "Forbidden"}), 403

    tasks = project.tasks
    return jsonify({
        "total": len(tasks),
        "todo": sum(1 for t in tasks if t.status == "todo"),
        "doing": sum(1 for t in tasks if t.status == "doing"),
        "done": sum(1 for t in tasks if t.status == "done"),
        "high_priority": sum(1 for t in tasks if t.priority == "high"),
        "members": len(project.members),
    }), 200


# ── Helpers ────────────────────────────────────────────────────────────────────
def _can_access(user_id, project):
    user = User.query.get(user_id)
    if not user:
        return False
    if user.role == "admin":
        return True
    return project.owner_id == user_id or any(m.id == user_id for m in project.members)


def _can_manage(user_id, project):
    user = User.query.get(user_id)
    if not user:
        return False
    return user.role == "admin" or project.owner_id == user_id