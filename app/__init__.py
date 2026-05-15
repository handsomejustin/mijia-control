import os

from dotenv import load_dotenv

load_dotenv()

from config import config_map


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    from flask import Flask

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    _init_extensions(app)
    _register_blueprints(app)
    _register_cli(app)
    _register_error_handlers(app)
    _add_security_headers(app)

    if config_name != "testing":
        from app.services.energy_poller import start_energy_poller

        start_energy_poller(app)

    return app


def _init_extensions(app):
    from app.extensions import csrf, db, jwt, limiter, login_manager, migrate, socketio

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app)

    from flasgger import Swagger
    Swagger(app)

    import app.web.socketio  # noqa: F401 — 注册 SocketIO 事件处理

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return db.session.get(User, int(user_id))


def _register_blueprints(app):
    from app.api import api_bp
    from app.web import web_bp
    from app.web.admin import admin_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(web_bp)
    app.register_blueprint(admin_bp)


def _register_cli(app):
    from app.cli import register_cli

    register_cli(app)


def _register_error_handlers(app):
    from flask import jsonify, render_template

    @app.errorhandler(404)
    def not_found(e):
        if _wants_json_response():
            return jsonify(error="Not found"), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        if _wants_json_response():
            return jsonify(error="Forbidden"), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def internal_error(e):
        if _wants_json_response():
            return jsonify(error="Internal server error"), 500
        return render_template("errors/500.html"), 500


def _add_security_headers(app):
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        go2rtc_url = app.config.get("GO2RTC_URL", "")
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net "
            "https://cdn.socket.io; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com "
            "https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; "
            f"frame-src 'self' {go2rtc_url}; "
            "frame-ancestors 'self';"
        )
        if not app.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


def _wants_json_response():
    from flask import request

    return (
        request.accept_mimetypes.best_match(["application/json", "text/html"])
        == "application/json"
    )
