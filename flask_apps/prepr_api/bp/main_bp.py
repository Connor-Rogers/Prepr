from flask import Blueprint, request, jsonify
from lib.iam import verify_token
from lib.firebase import db

main = Blueprint("main_bp", __name__)


@main.route("/")
def index():
    return "Hello World!"


from flask import Flask, request, jsonify, _request_ctx_stack
from jose import jwt
import requests

AUTH0_DOMAIN = "<YOUR_AUTH0_DOMAIN>"
AUTH0_API_AUDIENCE = "<YOUR_AUTH0_API_AUDIENCE>"
ALGORITHMS = ["RS256"]

app = Flask(__name__)


def get_jwt():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        return None

    parts = auth.split()

    if parts[0].lower() != "bearer":
        return None
    elif len(parts) == 1:
        return None
    elif len(parts) > 2:
        return None

    token = parts[1]
    return token


def verify_user(f):
    """Determines if the Access Token is valid"""

    def wrapper(*args, **kwargs):
        token = get_jwt()
        if token is None:
            return (
                jsonify(
                    {
                        "code": "authorization_header_missing",
                        "description": "Authorization header is expected",
                    }
                ),
                401,
            )

        jsonurl = requests.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
        jwks = jsonurl.json()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }

        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=AUTH0_API_AUDIENCE,
                    issuer=f"https://{AUTH0_DOMAIN}/",
                )
            except Exception as e:
                return jsonify({"code": "invalid_header", "description": str(e)}), 401

            _request_ctx_stack.top.current_user = payload
            return f(*args, **kwargs)

        return (
            jsonify(
                {
                    "code": "invalid_header",
                    "description": "Unable to find the appropriate key",
                }
            ),
            401,
        )

    return wrapper


@app.route("/v1/secure/submit-macros", methods=["POST"])
@verify_user
def submit_macros():
    # Example: do something with the posted data
    data = request.json
    return jsonify({"message": "Data received", "data": data})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

# @main.route("/v1/secure/submit-macros", methods=["POST"])
# @verify_token
# def submit_macros(payload):
#     # You can access user information from the payload
#     user_id = payload.get("sub")  # sub usually contains the user id

#     data = request.json
#     # Save data to Firebase with user information
#     macros_ref = db.collection("macro_calc")
#     macros_ref.add({"user_id": user_id, "macros": data})

#     return jsonify({"message": "Data saved successfully"}), 200
