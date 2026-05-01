from flask import Blueprint

api_bp = Blueprint("api", __name__)

from app.api.auth import auth_ns
from app.api.auth_jwt import auth_jwt_ns
from app.api.xiaomi_auth import xiaomi_ns
from app.api.devices import devices_ns
from app.api.homes import homes_ns
from app.api.scenes import scenes_ns
from app.api.tokens import tokens_ns
from app.api.device_groups import device_groups_bp
from app.api.automations import automations_bp
from app.api.energy import energy_bp

api_bp.register_blueprint(auth_ns)
api_bp.register_blueprint(auth_jwt_ns)
api_bp.register_blueprint(xiaomi_ns)
api_bp.register_blueprint(devices_ns)
api_bp.register_blueprint(homes_ns)
api_bp.register_blueprint(scenes_ns)
api_bp.register_blueprint(tokens_ns)
api_bp.register_blueprint(device_groups_bp)
api_bp.register_blueprint(automations_bp)
api_bp.register_blueprint(energy_bp)
