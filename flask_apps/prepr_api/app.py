"""
WSGI Application Module

This module sets up and initializes the main Flask application for the server. 
Configuration values for Flask are specified, and CORS is set up to allow cross-origin requests.
The module also imports and registers multiple blueprints that likely handle different parts of the application.

Dependencies:
    - flask: A lightweight WSGI web application framework.
    - flask_cors: An extension for Flask that adds support for handling Cross-Origin Resource Sharing (CORS).

Functions:
    - app_factory(): Factory function for creating and configuring the Flask app instance.
"""
import flask
from flask_cors import CORS


def app_factory():
    """
    Factory function to create and configure a Flask app instance.

    Returns:
        flask.Flask: Configured Flask app instance.
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
    from bp.planner_bp import meal_plan

    app.register_blueprint(meal_plan)
    app.register_blueprint(main)
    app.register_blueprint(profile)
    app.register_blueprint(recipe)

    return app


if __name__ == "__main__":
    app = app_factory()
    app.run()
