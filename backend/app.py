import os
from pathlib import Path

from flask import Flask

from backend import db
from backend.config import Config
from backend.routes import main


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app(test_config=None, register_blueprint=True):
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "frontend"),
        static_folder="../frontend",
        static_url_path="/static",
    )
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    if register_blueprint:
        app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    return app


app = create_app(register_blueprint=False)
app.register_blueprint(main)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
