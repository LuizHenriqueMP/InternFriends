from datetime import datetime, timezone

from app.extensions import db


class Comment(db.Model):
    __tablename__ = "comments"
    __table_args__ = (
        db.UniqueConstraint("author_id", "publication_date", name="uq_comment_author_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)
    publication_date = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)

    author = db.relationship("User", back_populates="comments")
    votes = db.relationship("CommentVote", back_populates="comment", cascade="all, delete-orphan", lazy="dynamic")
