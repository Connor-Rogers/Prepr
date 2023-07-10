from functools import wraps
from flask import request, jsonify, g
from firebase_admin import auth, credentials
import firebase_admin


def firebase_auth_required(f):
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
