# Main WSGI Application
import flask
from flask import Blueprint


def app_factory():
    """
    Create Flask app
    """

    app = flask.Flask(__name__)
    app.config = {
        "DEBUG": True
    }

    return app


if __name__ == '__main__':
    app = app_factory()
    app.run()
