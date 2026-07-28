import uuid
from datetime import datetime, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.extensions import db


_password_hasher = PasswordHasher()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    public_uuid = db.Column(
        db.String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    email = db.Column(db.String(320), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(512), nullable=True)
    status = db.Column(
        db.String(32),
        nullable=False,
        default="pending_verification",
        index=True,
    )
    is_admin = db.Column(db.Boolean, nullable=False, default=False, index=True)
    email_verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    comments = db.relationship("Comment", back_populates="author", lazy="dynamic")
    votes = db.relationship("CommentVote", back_populates="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = _password_hasher.hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        try:
            return _password_hasher.verify(self.password_hash, password)
        except VerifyMismatchError:
            return False

    @property
    def is_active(self) -> bool:
        return self.status == "active" and self.deleted_at is None
