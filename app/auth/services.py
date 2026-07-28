import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app

from app.extensions import db
from app.models import AccountToken, User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def email_domain_allowed(email: str) -> bool:
    try:
        local, domain = normalize_email(email).rsplit("@", 1)
    except ValueError:
        return False
    return bool(local) and domain in current_app.config["ALLOWED_EMAIL_DOMAINS"]


def validate_password(password: str) -> str | None:
    if len(password) < 10:
        return "A senha deve ter pelo menos 10 caracteres."
    if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
        return "A senha deve conter letras e números."
    return None


def create_account_token(user: User, purpose: str, lifetime_minutes: int) -> str:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token = AccountToken(
        user_id=user.id,
        purpose=purpose,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=lifetime_minutes),
    )
    db.session.add(token)
    db.session.commit()
    return raw_token


def consume_account_token(raw_token: str, purpose: str) -> AccountToken | None:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token = AccountToken.query.filter_by(token_hash=token_hash, purpose=purpose).first()
    now = datetime.now(timezone.utc)
    if not token or token.used_at is not None:
        return None
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        return None
    token.used_at = now
    db.session.commit()
    return token
