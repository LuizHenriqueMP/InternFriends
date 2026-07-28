from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError

from app.extensions import db, limiter
from app.models import Comment, CommentVote, User


comments_bp = Blueprint("comments", __name__, url_prefix="/api/comments")


def _user() -> User | None:
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity)) if identity else None
    return user if user and user.is_active else None


def _today_local():
    return datetime.now(ZoneInfo(current_app.config["TIMEZONE"])).date()


@comments_bp.get("")
@jwt_required()
def list_comments():
    user = _user()
    if not user:
        return jsonify(message="Conta indisponível."), 401

    likes = func.coalesce(func.sum(case((CommentVote.value == 1, 1), else_=0)), 0)
    dislikes = func.coalesce(func.sum(case((CommentVote.value == -1, 1), else_=0)), 0)
    rows = (
        db.session.query(Comment, likes.label("likes"), dislikes.label("dislikes"))
        .outerjoin(CommentVote, CommentVote.comment_id == Comment.id)
        .filter(Comment.deleted_at.is_(None))
        .group_by(Comment.id)
        .order_by(Comment.created_at.desc())
        .all()
    )
    my_votes = {
        vote.comment_id: vote.value
        for vote in CommentVote.query.filter_by(user_id=user.id).all()
    }
    return jsonify(
        comments=[
            {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at.isoformat(),
                "likes": int(like_count),
                "dislikes": int(dislike_count),
                "my_vote": my_votes.get(comment.id),
                "can_delete": comment.author_id == user.id or user.is_admin,
                "author_email": comment.author.email if user.is_admin else None,
            }
            for comment, like_count, dislike_count in rows
        ]
    )


@comments_bp.post("")
@jwt_required()
@limiter.limit("10 per minute")
def create_comment():
    user = _user()
    if not user:
        return jsonify(message="Conta indisponível."), 401
    content = ((request.get_json(silent=True) or {}).get("content") or "").strip()
    if not content:
        return jsonify(message="O comentário não pode ficar vazio."), 400
    if len(content) > current_app.config["COMMENT_MAX_LENGTH"]:
        return jsonify(message="O comentário ultrapassa o limite permitido."), 400
    comment = Comment(author_id=user.id, content=content, publication_date=_today_local())
    db.session.add(comment)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message="Você já publicou um comentário hoje."), 409
    return jsonify(id=comment.id, message="Comentário publicado."), 201


@comments_bp.delete("/<int:comment_id>")
@jwt_required()
def delete_comment(comment_id: int):
    user = _user()
    comment = db.session.get(Comment, comment_id)
    if not user:
        return jsonify(message="Conta indisponível."), 401
    if not comment or comment.deleted_at is not None:
        return jsonify(message="Comentário não encontrado."), 404
    if comment.author_id != user.id and not user.is_admin:
        return jsonify(message="Você não pode excluir este comentário."), 403
    comment.deleted_at = datetime.now(timezone.utc)
    comment.content = None
    db.session.commit()
    return jsonify(message="Comentário excluído.")


@comments_bp.put("/<int:comment_id>/vote")
@jwt_required()
def vote(comment_id: int):
    user = _user()
    comment = db.session.get(Comment, comment_id)
    if not user:
        return jsonify(message="Conta indisponível."), 401
    if not comment or comment.deleted_at is not None:
        return jsonify(message="Comentário não encontrado."), 404
    value = (request.get_json(silent=True) or {}).get("value")
    if value not in (-1, 1):
        return jsonify(message="O voto deve ser 1 ou -1."), 400

    existing = CommentVote.query.filter_by(comment_id=comment.id, user_id=user.id).first()
    if existing and existing.value == value:
        db.session.delete(existing)
        action = "removido"
    elif existing:
        existing.value = value
        action = "alterado"
    else:
        db.session.add(CommentVote(comment_id=comment.id, user_id=user.id, value=value))
        action = "registrado"
    db.session.commit()
    return jsonify(message=f"Voto {action}.")


@comments_bp.delete("/<int:comment_id>/vote")
@jwt_required()
def remove_vote(comment_id: int):
    user = _user()
    if not user:
        return jsonify(message="Conta indisponível."), 401
    vote = CommentVote.query.filter_by(comment_id=comment_id, user_id=user.id).first()
    if vote:
        db.session.delete(vote)
        db.session.commit()
    return jsonify(message="Voto removido.")
