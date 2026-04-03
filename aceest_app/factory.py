import os
from typing import Optional

from flask import Flask

from aceest_app.db import close_db, get_db, init_db
from aceest_app.routes import api_bp


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)

    default_db_path = os.environ.get("ACEEST_DB_PATH", os.path.join(os.getcwd(), "aceest.db"))
    app.config.update(
        TESTING=False,
        DB_PATH=default_db_path,
        JSON_SORT_KEYS=False,
    )

    if test_config:
        app.config.update(test_config)

    @app.teardown_appcontext
    def _close_db(_exc):
        close_db()

    app.register_blueprint(api_bp)

    with app.app_context():
        conn = get_db()
        init_db(conn)

    return app

