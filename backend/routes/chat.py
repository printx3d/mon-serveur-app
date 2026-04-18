from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models import Message, Project, User, Notification

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/<int:project_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)

    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    messages = (
        Message.query
        .filter_by(project_id=project_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return jsonify([m.to_dict() for m in messages]), 200


@chat_bp.route("/<int:project_id>/messages", methods=["POST"])
@jwt_required()
def send_message(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)
    data = request.get_json()

    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Message content cannot be empty"}), 400
    if len(content) > 2000:
        return jsonify({"error": "Message too long (max 2000 chars)"}), 400

    message = Message(
        content=content,
        project_id=project_id,
        sender_id=user_id,
    )
    db.session.add(message)
    db.session.commit()
    return jsonify(message.to_dict()), 201


@chat_bp.route("/<int:project_id>/messages/<int:message_id>", methods=["DELETE"])
@jwt_required()
def delete_message(project_id, message_id):
    user_id = int(get_jwt_identity())
    message = Message.query.get_or_404(message_id)

    user = User.query.get(user_id)
    if message.sender_id != user_id and user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(message)
    db.session.commit()
    return jsonify({"message": "Message deleted"}), 200