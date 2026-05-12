"""Entrypoint for the rebuilt backend."""

from __future__ import annotations

from . import create_app


app = create_app()


if __name__ == "__main__":
    settings = app.config["SETTINGS"]
    app.run(host=settings.flask_host, port=settings.flask_port, debug=settings.debug)
