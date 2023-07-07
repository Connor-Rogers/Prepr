# Main WSGI Application
import flask
from flask import Blueprint
from flask_cors import CORS
from firebase_admin import credentials
import firebase_admin


def app_factory():
    """
    Create Flask app
    """

    app = flask.Flask(__name__)
    app.config = {
        "SECRET_KEY": "secret",
        "DEBUG": True,
        "SERVER_NAME": "127.0.0.1:5000",
        "PROPAGATE_EXCEPTIONS": True,
        "APPLICATION_ROOT": "/v1",
        "PREFERRED_URL_SCHEME": "http",
        "SESSION_COOKIE_NAME": "session",
        "SESSION_COOKIE_DOMAIN": ".localhost",
        "SESSION_COOKIE_PATH": "/",
        "SESSION_COOKIE_SECURE": False,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_REFRESH_EACH_REQUEST": True,
        "SESSION_COOKIE_HTTPONLY": True,
        "TRAP_HTTP_EXCEPTIONS": True,
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
    }
    CORS(
        app,
        resources={r"/profile/*": {"origins": "http://localhost:3000"}},
        supports_credentials=True,
    )
    from bp.main_bp import main

    app.register_blueprint(main)
    # try:
    #     cred = credentials.Certificate("prepr_fb_secret.json")
    #     firebase_admin.initialize_app(cred)
    # except ValueError:
    #     pass

    return app


if __name__ == "__main__":
    app = app_factory()
    app.run()
