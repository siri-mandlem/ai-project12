import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTANCE_PATH = PROJECT_ROOT / "instance"
INSTANCE_PATH.mkdir(exist_ok=True)


def normalize_database_url(database_url):
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    if database_url.startswith(("postgresql+psycopg://", "postgres+psycopg://")):
        return database_url.replace("+psycopg://", "+psycopg2://", 1)
    return database_url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-development-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{(INSTANCE_PATH / 'library.db').as_posix()}",
    )
    SQLALCHEMY_DATABASE_URI = normalize_database_url(SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.environ.get("FLASK_ENV") == "production"
        or os.environ.get("RENDER", "").lower() == "true"
    )
