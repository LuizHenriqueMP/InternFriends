import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://quadro:quadro@127.0.0.1:3306/quadro_comentarios?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    ALLOWED_EMAIL_DOMAINS = {
        item.strip().lower()
        for item in os.getenv("ALLOWED_EMAIL_DOMAINS", "empresa.com.br").split(",")
        if item.strip()
    }
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
    MAIL_BACKEND = os.getenv("MAIL_BACKEND", "console").lower()
    MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@example.com")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    COMMENT_MAX_LENGTH = int(os.getenv("COMMENT_MAX_LENGTH", "1000"))
    TOKEN_EXPIRATION_MINUTES = int(os.getenv("TOKEN_EXPIRATION_MINUTES", "60"))
    PASSWORD_RESET_EXPIRATION_MINUTES = int(
        os.getenv("PASSWORD_RESET_EXPIRATION_MINUTES", "30")
    )
    TIMEZONE = os.getenv("TIMEZONE", "America/Sao_Paulo")
