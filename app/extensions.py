from flask import request
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


@limiter.request_filter
def _exempt_internal_clients():
    ip = request.remote_addr or ""
    return (
        ip == "127.0.0.1"
        or ip == "::1"
        or ip.startswith("10.")
        or ip.startswith("172.")
        or ip.startswith("192.168.")
    )

login_manager.login_view = "web.login"
login_manager.login_message = "请先登录"
