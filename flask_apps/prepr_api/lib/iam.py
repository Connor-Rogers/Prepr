from functools import wraps
from flask import request, jsonify, g
from firebase_admin import auth


def firebase_auth_required(f):
    """
    Decorator to ensure that a valid Firebase ID token is present in the request's
    Authorization header. This token is verified using the Firebase Admin SDK's `verify_id_token` method.

    If the token is valid, the decoded token is added to Flask's global `g` object
    as `g.user`, allowing the view function to access the authenticated user's details.

    If the token is missing or invalid, a JSON error response is returned with appropriate
    status codes (403 for missing token and 401 for invalid token).

    Usage:
        @firebase_auth_required
        def some_route():
            user = g.user
            # rest of the view function

    :param f: The view function to decorate.
    :return: The decorated function.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        id_token = request.headers.get("Authorization")

        if not id_token:
            return jsonify({"message": "Token is missing"}), 403

        try:
            id_token = id_token.split("Bearer ")[1]

            decoded_token = auth.verify_id_token(id_token)
            g.user = decoded_token
        except ValueError as e:
            return jsonify({"message": "Invalid token", "error": str(e)}), 401

        return f(*args, **kwargs)

    return decorated_function
