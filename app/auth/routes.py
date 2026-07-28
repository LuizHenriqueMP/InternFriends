from datetime import datetime, timezone

from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from app.auth.services import (
    consume_account_token,
    create_account_token,
    email_domain_allowed,
    normalize_email,
    validate_password,
)
from app.email.service import send_email
from app.extensions import db, limiter
from app.models import User


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _current_user() -> User | None:
    identity = get_jwt_identity()
    return db.session.get(User, int(identity)) if identity else None


def _send_verification(user: User) -> None:
    raw_token = create_account_token(
        user, "verify_email", current_app.config["TOKEN_EXPIRATION_MINUTES"]
    )
    link = f'{current_app.config["APP_BASE_URL"]}/api/auth/verify-email?token={raw_token}'
    send_email(user.email, "Confirme seu e-mail", f"Confirme sua conta acessando: {link}")


@auth_bp.post("/register")
@limiter.limit("5 per minute")
def register():
    payload = request.get_json(silent=True) or {}
    email = normalize_email(payload.get("email", ""))
    password = payload.get("password", "")
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify(message="E-mail inválido."), 400
    if not email_domain_allowed(email):
        return jsonify(message="O domínio do e-mail não é permitido."), 400
    password_error = validate_password(password)
    if password_error:
        return jsonify(message=password_error), 400
    if User.query.filter_by(email=email).first():
        return jsonify(message="Já existe uma conta com esse e-mail."), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message="Já existe uma conta com esse e-mail."), 409
    _send_verification(user)
    return jsonify(message="Conta criada. Verifique seu e-mail."), 201


@auth_bp.get("/verify-email")
def verify_email():
    token = request.args.get("token", "")
    account_token = consume_account_token(token, "verify_email")
    if not account_token:
        return jsonify(message="Token inválido ou expirado."), 400
    user = account_token.user
    if user.status == "deleted":
        return jsonify(message="Conta indisponível."), 400
    user.status = "active"
    user.email_verified_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(message="E-mail verificado com sucesso.")


@auth_bp.post("/resend-verification")
@limiter.limit("3 per hour")
def resend_verification():
    email = normalize_email((request.get_json(silent=True) or {}).get("email", ""))
    user = User.query.filter_by(email=email, status="pending_verification").first()
    if user:
        _send_verification(user)
    return jsonify(message="Caso a conta esteja pendente, enviaremos um novo link.")


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    payload = request.get_json(silent=True) or {}
    email = normalize_email(payload.get("email", ""))
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(payload.get("password", "")):
        return jsonify(message="E-mail ou senha inválidos."), 401
    if not user.is_active:
        return jsonify(message="A conta ainda não está ativa."), 403
    return jsonify(access_token=create_access_token(identity=str(user.id)))


@auth_bp.post("/forgot-password")
@limiter.limit("5 per hour")
def forgot_password():
    email = normalize_email((request.get_json(silent=True) or {}).get("email", ""))
    user = User.query.filter_by(email=email, status="active").first()
    if user:
        raw_token = create_account_token(
            user,
            "reset_password",
            current_app.config["PASSWORD_RESET_EXPIRATION_MINUTES"],
        )
        link = f'{current_app.config["APP_BASE_URL"]}/reset-password?token={raw_token}'
        send_email(user.email, "Recuperação de senha", f"Defina uma nova senha acessando: {link}")
    return jsonify(message="Caso o e-mail esteja cadastrado, enviaremos as instruções.")


@auth_bp.post("/reset-password")
def reset_password():
    payload = request.get_json(silent=True) or {}
    password_error = validate_password(payload.get("password", ""))
    if password_error:
        return jsonify(message=password_error), 400
    account_token = consume_account_token(payload.get("token", ""), "reset_password")
    if not account_token or account_token.user.status != "active":
        return jsonify(message="Token inválido ou expirado."), 400
    account_token.user.set_password(payload["password"])
    db.session.commit()
    return jsonify(message="Senha alterada com sucesso.")


@auth_bp.get("/me")
@jwt_required()
def me():
    user = _current_user()
    if not user or not user.is_active:
        return jsonify(message="Conta indisponível."), 401
    return jsonify(id=user.public_uuid, email=user.email, status=user.status, is_admin=user.is_admin)


@auth_bp.delete("/account")
@jwt_required()
def delete_account():
    user = _current_user()
    if not user or not user.is_active:
        return jsonify(message="Conta indisponível."), 401
    user.email = None
    user.password_hash = None
    user.status = "deleted"
    user.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(message="Conta excluída e anonimizada.")
