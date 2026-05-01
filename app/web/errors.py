from flask import render_template

from app.web import web_bp


@web_bp.app_errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403


@web_bp.app_errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404


@web_bp.app_errorhandler(500)
def internal_error(e):
    return render_template("errors/500.html"), 500
