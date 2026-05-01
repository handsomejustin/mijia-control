from flask import Blueprint

web_bp = Blueprint("web", __name__, template_folder="../templates", static_folder="../static")

from app.web.routes import register_routes

register_routes(web_bp)
