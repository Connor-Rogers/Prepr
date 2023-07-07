from flask import Blueprint, request, jsonify
from lib.iam import firebase_auth_required

main = Blueprint("main_bp", __name__)


@main.route("/")
def index():
    return "Hello World!"


@firebase_auth_required
@main.route("/profile", methods=["POST"])
def create_profile():
    data = request.json
    # Here you can save the data to a database
    print("Received data:", data)

    return jsonify({"message": "Profile data received"})
