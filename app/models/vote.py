from datetime import datetime, timezone

from app.extensions import db


class CommentVote(db.Model):
    __tablename__ = "comment_votes"
    __table_args__ = (
        db.UniqueConstraint("comment_id", "user_id", name="uq_vote_comment_user"),
        db.CheckConstraint("value IN (-1, 1)", name="ck_vote_value"),
    )

    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    value = db.Column(db.SmallInteger, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    comment = db.relationship("Comment", back_populates="votes")
    user = db.relationship("User", back_populates="votes")
