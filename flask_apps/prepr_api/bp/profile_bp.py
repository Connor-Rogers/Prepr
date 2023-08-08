from datetime import timedelta
from flask import Blueprint, request, jsonify, g
from werkzeug.datastructures import FileStorage
from PIL import Image
import io, re
from decouple import config

from lib.firebase import buckit, db
from lib.iam import firebase_auth_required
from lib.macro import macro_calculator

profile = Blueprint("profile_bp", __name__)


@profile.route("/profile/get", methods=["GET"])
@firebase_auth_required
def get_profile():
    """
    Retrieve the profile data for the authenticated user.

    Returns:
        dict: Profile data if found.
        dict: Error message if the profile is not found.
    """
    # ... code ...
    # get user data
    user_id = g.user.get("user_id")  # getting user_id
    doc_ref = db.collection("profile").document(user_id)
    profile = doc_ref.get()

    if profile.exists:
        return jsonify(profile.to_dict()), 200
    else:
        return jsonify({"error": "Profile not found"}), 404


@profile.route("/profile/goals", methods=["POST"])
@firebase_auth_required
def update_goals():
    """
    Update the fitness goals of the authenticated user based on the given parameters.

    Expected JSON:
        heightin, heightft, weight, age, activity, gender, goal

    Returns:
        dict: Success message if the goals are updated successfully.
        dict: Error message if the input data is invalid.
    """
    user_id = g.user.get("user_id")  # getting user_id

    # Extract data from the request
    try:
        height_in = int(request.json.get("heightin"))
        height_ft = int(request.json.get("heightft"))
        weight = int(request.json.get("weight"))
        age = int(request.json.get("age"))
        activity = str(request.json.get("activity"))
        gender = str(request.json.get("gender"))
        goal = str(request.json.get("goal"))
    except ValueError:
        return jsonify({"error": "Invalid input"}), 400

    # Get the document reference
    doc_ref = db.collection("profile").document(user_id)

    # Update the fields
    doc_ref.update(
        {
            "height_in": height_in,
            "height_ft": height_ft,
            "weight": weight,
            "age": age,
            "activity": activity,
            "gender": gender,
            "goal": goal,
            "macros": macro_calculator(
                height_in=height_in,
                height_ft=height_ft,
                weight=weight,
                age=age,
                activity=activity,
                gender=gender,
                goal=goal,
            ),
        }
    )

    return jsonify({"message": "Profile goals updated"}), 200


@profile.route("/profile/insert", methods=["POST"])
@firebase_auth_required
def create_or_update_profile():
    """
    Create or update the profile for the authenticated user. This also handles
    the uploading of an image for the user's profile picture.

    Form Data:
        name: Name of the user.
        image: Image file to be used as the user's profile picture.

    Returns:
        dict: Success message if the profile data and image are successfully received and stored.
        dict: Error message if there's an issue with the provided data.
    """
    name = request.form.get("name")  # getting name from form data
    image = request.files.get("image", None)  # getting image from form data

    user_id = g.user.get("user_id")  # getting user_id

    # Name validation
    if name and not re.match("^[a-zA-Z0-9 ]*$", name):
        return jsonify({"error": "Invalid name"}), 400

    # Check the file type
    if image:
        file_ext = image.filename.split(".")[-1]
        try:
            Image.open(image)
            image.seek(0)
        except IOError:
            return jsonify({"error": "The file is not an image"}), 400

        # convert image data to bytes
        if isinstance(image, FileStorage):
            image_bytes = io.BytesIO()
            image.save(image_bytes)
            image_bytes.seek(0)

        # Delete old photo if exists
        bucket = buckit.get_bucket(config("GCLOUD_BUKIT"))
        old_blob_name = f"profile/{user_id}/photo.{file_ext}"
        old_blob = bucket.blob(old_blob_name)
        if old_blob.exists():
            old_blob.delete()

        # upload the new image to Google Cloud Storage
        destination_blob_name = f"profile/{user_id}/photo.{file_ext}"
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_file(image_bytes, content_type=image.content_type)

    # Get the document reference
    doc_ref = db.collection("profile").document(user_id)

    # Create or update the profile with default values
    doc_ref.set(
        {
            "height_in": 0,
            "height_ft": 0,
            "weight": 0,
            "age": 0,
            "activity": "sedentary",
            "gender": "male",
            "goal": "lose",
            "macros": {"calories": 0, "carbs": 0, "protein": 0, "fat": 0},
            "liked_recipies": [],
        },
        merge=True,
    )

    # Set the name if provided
    if name:
        doc_ref.set({"name": name}, merge=True)

    return (
        jsonify({"message": "Profile data received and image uploaded to Firebase"}),
        200,
    )


@profile.route("/profile/get/photo", methods=["GET"])
@firebase_auth_required
def get_icon():
    """
    Retrieve the profile picture URL for the authenticated user.

    Returns:
        dict: Profile data including the image URL if found.
        dict: Error message if the profile or image is not found.
    """
    user_id = g.user.get("user_id")
    doc_ref = db.collection("profile").document(user_id)

    try:
        doc = doc_ref.get()
        if doc.exists:
            profile_data = doc.to_dict()

            # Fetch the image url from Firebase storage
            bucket = buckit.get_bucket(config("GCLOUD_BUKIT"))

            # Get a list of all blobs in the 'profile/{user_id}' directory
            blobs = bucket.list_blobs(prefix=f"profile/{user_id}")

            # Ensure there is at least one blob in the directory
            blob = next(blobs, None)
            if blob:
                image_url = blob.generate_signed_url(
                    timedelta(seconds=300), method="GET"
                )
                profile_data["image_url"] = image_url

            return jsonify(profile_data), 200
        else:
            return jsonify({"error": "Profile not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@profile.route("/profile/get/username", methods=["GET"])
@firebase_auth_required
def get_username():
    """
    Retrieve the username for the authenticated user.

    Returns:
        dict: Username of the authenticated user if found.
        dict: Error message if the profile is not found.
    """
    user_id = g.user.get("user_id")
    doc_ref = db.collection("profile").document(user_id)

    try:
        doc = doc_ref.get()
        if doc.exists:
            profile_data = doc.to_dict()
            username = profile_data.get("name", "")
            return jsonify({"username": username}), 200
        else:
            return jsonify({"error": "Profile not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@profile.route("/profile/get/photo/<other_user_id>", methods=["GET"])
@firebase_auth_required
def get_other_icon(other_user_id):
    """
    Retrieve the profile picture URL for a specific user that is not the active user.

    Parameters:
        other_user_id (str): User ID of the user whose profile picture URL is to be fetched.

    Returns:
        dict: Profile data including the image URL if found.
        dict: Error message if the profile or image is not found.
    """
    doc_ref = db.collection("profile").document(other_user_id)

    try:
        doc = doc_ref.get()
        if doc.exists:
            profile_data = doc.to_dict()

            # Fetch the image url from Firebase storage
            bucket = buckit.get_bucket(config("GCLOUD_BUKIT"))

            # Get a list of all blobs in the 'profile/{other_user_id}' directory
            blobs = bucket.list_blobs(prefix=f"profile/{other_user_id}")

            # Ensure there is at least one blob in the directory
            blob = next(blobs, None)
            if blob:
                image_url = blob.generate_signed_url(
                    timedelta(seconds=300), method="GET"
                )
                profile_data["image_url"] = image_url

            return jsonify(profile_data), 200
        else:
            return jsonify({"error": "Profile not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
