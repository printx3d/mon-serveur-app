from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import bcrypt

from app import db
from models import User

users_bp = Blueprint("users", __name__)


def require_admin(user_id):
    user = User.query.get(user_id)
    return user and user.role == "admin"


@users_bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    users = User.query.order_by(User.username).all()
    return jsonify([u.to_dict() for u in users]), 200


@users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict(include_email=True)), 200


@users_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    current_id = int(get_jwt_identity())
    is_admin = require_admin(current_id)

    # Users can only edit themselves, admins can edit anyone
    if current_id != user_id and not is_admin:
        return jsonify({"error": "Forbidden"}), 403

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if "username" in data:
        new_username = data["username"].strip()
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != user_id:
            return jsonify({"error": "Username already taken"}), 409
        user.username = new_username

    if "email" in data:
        new_email = data["email"].strip().lower()
        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != user_id:
            return jsonify({"error": "Email already registered"}), 409
        user.email = new_email

    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        user.password_hash = bcrypt.hashpw(
            data["password"].encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    if "avatar_color" in data:
        user.avatar_color = data["avatar_color"]

    # Only admin can change roles
    if "role" in data and is_admin:
        if data["role"] in ("admin", "member"):
            user.role = data["role"]

    db.session.commit()
    return jsonify(user.to_dict(include_email=True)), 200


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_id = int(get_jwt_identity())
    if not require_admin(current_id):
        return jsonify({"error": "Admin required"}), 403

    user = User.query.get_or_404(user_id)
    if user.id == current_id:
        return jsonify({"error": "Cannot delete yourself"}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200


@users_bp.route("/online", methods=["GET"])
@jwt_required()
def online_users():
    from datetime import datetime, timedelta
    # Consider online if last_seen within 2 minutes
    threshold = datetime.utcnow() - timedelta(minutes=2)
    users = User.query.filter(User.last_seen >= threshold).all()
    return jsonify([u.to_dict() for u in users]), 200