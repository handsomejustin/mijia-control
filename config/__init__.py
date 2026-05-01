import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 days
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = False
    RATELIMIT_STORAGE_URI = "memory://"
    MIJIA_SPEC_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "instance", "spec_cache")
    SWAGGER = {
        "title": "米家控制 API",
        "version": "2.0.0",
        "description": "米家智能设备控制系统 RESTful API 文档",
        "uiversion": 3,
        "specs_route": "/api/docs/",
    }
    GO2RTC_URL = os.environ.get("GO2RTC_URL", "http://127.0.0.1:1984")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///test.db")
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
