import click
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

from app.config import Config
from app.extensions import db, jwt, limiter, migrate


def create_app(test_config: dict | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from app.auth.routes import auth_bp
    from app.comments.routes import comments_bp
    from app.admin_routes import admin_bp
    from app import models  # noqa: F401
    from app.models import User

    app.register_blueprint(auth_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(admin_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/reset-password")
    def reset_password_page():
        return render_template("index.html")

    @app.get("/admin")
    def admin_page():
        return render_template("admin.html")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        click.echo("Banco inicializado.")

    @app.cli.command("promote-admin")
    @click.option("--email", required=True, help="E-mail da conta que será administradora.")
    def promote_admin_command(email: str):
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            raise click.ClickException("Usuário não encontrado.")
        user.is_admin = True
        user.status = "active"
        db.session.commit()
        click.echo(f"{user.email} agora é administrador.")

    return app
