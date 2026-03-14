from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template

from .hardware import system_info_dict


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )

    @app.get("/health")
    def health() -> tuple[dict, int]:
        return {"status": "ok"}, 200

    @app.get("/api/system")
    def api_system() -> tuple[dict, int]:
        return jsonify(system_info_dict()), 200

    @app.get("/")
    def index():
        return render_template("index.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

