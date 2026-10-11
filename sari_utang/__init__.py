"""sari-utang: pautang list for a sari-sari store.

Layers (each only uses the ones below it):
  web/           Flask blueprints: pages and JSON API, login check
  services/      use cases (one class per area), commit when the work is done
  repositories/  all SQL, one class per table
  domain/        rules with no Flask or SQL: cleaning input, amounts, who owes what
"""

from flask import Flask, redirect, url_for

from sari_utang import cli, config, database, seed
from sari_utang.domain.money import peso, qty
from sari_utang.errors import register_error_handlers
from sari_utang.services import LoginThrottle
from sari_utang.web import BLUEPRINTS


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    config.configure(app, test_config)

    database.init_app(app)
    app.cli.add_command(cli.set_pin_command)
    app.cli.add_command(seed.seed_command)
    app.extensions["login_throttle"] = LoginThrottle()

    register_error_handlers(app)
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    # {{ amount|peso }} -> "₱12.50" and {{ item.quantity|qty }} -> "0.5" in templates.
    # The same functions format the PDF, so the page and the PDF show numbers the same way.
    app.add_template_filter(peso, "peso")
    app.add_template_filter(qty, "qty")

    @app.get("/favicon.ico")
    def favicon():
        """Browsers ask for /favicon.ico by themselves; send the app icon."""
        return app.send_static_file("icon.ico")

    return app
