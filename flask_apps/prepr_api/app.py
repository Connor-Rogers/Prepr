# Main WSGI Application
import flask
from flask import Blueprint
from flask_cors import CORS


def app_factory():
    """
    Create Flask app
    """

    app = flask.Flask(__name__)
    app.config = {
        "ENV": "development",
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
        "JSON_AS_ASCII": False,
        "PRESERVE_CONTEXT_ON_EXCEPTION": True,
        "JSON_SORT_KEYS": False,
        "JSONIFY_PRETTYPRINT_REGULAR": True,
        "JSONIFY_MIMETYPE": "application/json",
    }
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
    )
    from bp.main_bp import main
    from bp.profile_bp import profile
    from bp.recipe_bp import recipe

    app.register_blueprint(main)
    app.register_blueprint(profile)
    app.register_blueprint(recipe)

    # try:
    #     cred = credentials.Certificate("prepr_fb_secret.json")
    #     firebase_admin.initialize_app(cred)
    # except ValueError:
    #     pass

    return app


if __name__ == "__main__":
    app = app_factory()
    app.run()
