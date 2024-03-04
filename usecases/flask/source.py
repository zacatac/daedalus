from flask import Flask


def create_app():
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def hello_world():
        return "<p>Hello, World!</p>"

    return app
