from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Comment, User


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _current_admin() -> User | None:
    identity = get_jwt_identity()
    if not identity:
        return None
    try:
        user = db.session.get(User, int(identity))
    except (TypeError, ValueError):
        return None
    if not user or not user.is_active or not user.is_admin:
        return None
    return user


def admin_required(view):
    @wraps(view)
    @jwt_required()
    def wrapped(*args, **kwargs):
        admin = _current_admin()
        if not admin:
            return jsonify(message="Acesso restrito a administradores."), 403
        return view(admin, *args, **kwargs)

    return wrapped


@admin_bp.get("/users")
@admin_required
def list_users(admin: User):
    users = (
        User.query.filter(User.status != "deleted")
        .order_by(User.created_at.desc())
        .all()
    )
    return jsonify(
        users=[
            {
                "id": user.id,
                "public_uuid": user.public_uuid,
                "email": user.email,
                "status": user.status,
                "is_admin": user.is_admin,
                "email_verified_at": (
                    user.email_verified_at.isoformat()
                    if user.email_verified_at
                    else None
                ),
                "created_at": user.created_at.isoformat(),
            }
            for user in users
        ]
    )


@admin_bp.put("/users/<int:user_id>/activate")
@admin_required
def activate_user(admin: User, user_id: int):
    user = db.session.get(User, user_id)
    if not user or user.status == "deleted":
        return jsonify(message="Usuário não encontrado."), 404

    user.status = "active"
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify(message="Acesso do usuário liberado.")


@admin_bp.put("/users/<int:user_id>/block")
@admin_required
def block_user(admin: User, user_id: int):
    user = db.session.get(User, user_id)
    if not user or user.status == "deleted":
        return jsonify(message="Usuário não encontrado."), 404
    if user.id == admin.id:
        return jsonify(message="Você não pode bloquear sua própria conta."), 400

    user.status = "pending_verification"
    db.session.commit()
    return jsonify(message="Acesso do usuário bloqueado.")


@admin_bp.get("/comments")
@admin_required
def list_admin_comments(admin: User):
    comments = (
        Comment.query.filter(Comment.deleted_at.is_(None))
        .order_by(Comment.created_at.desc())
        .all()
    )
    return jsonify(
        comments=[
            {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at.isoformat(),
                "author_email": comment.author.email,
                "author_id": comment.author_id,
            }
            for comment in comments
        ]
    )


@admin_bp.delete("/comments/<int:comment_id>")
@admin_required
def delete_any_comment(admin: User, comment_id: int):
    comment = db.session.get(Comment, comment_id)
    if not comment or comment.deleted_at is not None:
        return jsonify(message="Comentário não encontrado."), 404

    comment.deleted_at = datetime.now(timezone.utc)
    comment.content = None
    db.session.commit()
    return jsonify(message="Comentário excluído pelo administrador.")
