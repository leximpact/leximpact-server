# -*- coding: utf-8 -*-

import connexion


def create_app() -> connexion.apps.flask_app.FlaskApp:
    app = connexion.App(__name__, specification_dir=".")
    app.add_api("api.yaml")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run()