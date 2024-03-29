from flask import Blueprint, request, jsonify, g
from datetime import timedelta
from decouple import config
import io, re
import datetime
import uuid

from lib.iam import firebase_auth_required
from lib.firebase import buckit, db

recipe = Blueprint("recipe_bp", __name__)


@recipe.route("/recipe/create", methods=["POST"])
@firebase_auth_required
def create_recipe():
    """
    Create a new recipe.

    Expects form data containing:
    - title: The title of the recipe.
    - instructions: The cooking instructions.
    - calories, fats, carbs, proteins: Nutritional information.
    - ingredients: Ingredients in the format ingredients[i][property_name].
    - photos[]: An array of photos.

    Returns:
    - JSON response with message and recipe_id.
    - HTTP status code.
    """
    # get the form data and convert it to a dictionary
    form_data = dict(request.form)

    # extract all keys that start with 'ingredients'
    ingredient_keys = [k for k in form_data.keys() if k.startswith("ingredients")]

    # initialize an empty list to hold your ingredients
    ingredients = []

    # process each ingredient key
    for k in ingredient_keys:
        # split the key into parts
        parts = k.split("[")

        # extract the index and property name
        index = int(parts[1][:-1])  # remove the trailing ']'
        prop = parts[2][:-1]  # remove the trailing ']'

        # extend the list of ingredients if necessary
        while index >= len(ingredients):
            ingredients.append({})
        # add the property to the appropriate ingredient
        ingredients[index][prop] = form_data[k]

    title = form_data.get("title")
    instructions = form_data.get("instructions")
    calories = form_data.get("calories")
    fats = form_data.get("fats")
    carbs = form_data.get("carbs")
    proteins = form_data.get("proteins")

    # getting recipe photos
    photos = request.files.getlist("photos[]")

    # creating a unique id for the recipe
    recipe_id = str(uuid.uuid4())

    bucket = buckit.get_bucket(config("GCLOUD_BUKIT"))
    photo_urls = []

    for i, photo in enumerate(photos):
        photo_bytes = io.BytesIO()
        photo.save(photo_bytes)
        photo_bytes.seek(0)
        blob_name = f"recipes/{recipe_id}/photo_{i}.jpg"
        blob = bucket.blob(blob_name)
        blob.upload_from_file(photo_bytes, content_type=photo.content_type)
        photo_urls.append(blob.public_url)

    doc_ref = db.collection("recipes").document(recipe_id)

    doc_ref.set(
        {
            "author": g.user.get("user_id"),
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": title,
            "instructions": instructions,
            "calories": calories,
            "fats": fats,
            "carbs": carbs,
            "proteins": proteins,
            "ingredients": ingredients,  # use the processed list of ingredients
            "photos": photo_urls,
        }
    )

    return (
        jsonify({"message": "Recipe created successfully", "recipe_id": recipe_id}),
        200,
    )


@recipe.route("/recipe/<string:document_id>/photos", methods=["GET"])
@firebase_auth_required
def get_recipe_photos(document_id):
    """
    Fetch photos associated with a given recipe document ID.

    Returns:
    - JSON response containing the photos URL or an error message.
    - HTTP status code.
    """
    doc_ref = db.collection("recipes").document(document_id)
    try:
        doc = doc_ref.get()
        if doc.exists:
            profile_data = doc.to_dict()

            # Fetch the image url from Firebase storage
            bucket = buckit.get_bucket(config("GCLOUD_BUKIT"))

            # Get a list of all blobs in the 'recipes/{document_id}' directory
            blobs = bucket.list_blobs(prefix=f"recipes/{document_id}")

            # Generate signed url for each blob and add to image_urls list
            image_urls = []
            for blob in blobs:
                image_url = blob.generate_signed_url(
                    timedelta(seconds=300), method="GET"
                )
                image_urls.append(image_url)

            profile_data["photos"] = image_urls

            return jsonify(profile_data), 200
        else:
            return jsonify({"error": "Recipe not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@recipe.route("/recipe/<recipe_id>/photos", methods=["POST"])
@firebase_auth_required
def add_photos(recipe_id):
    """
    Add photos to an existing recipe.

    Expects form data containing:
    - photos: An array of photos to add to the recipe.

    Returns:
    - JSON response with a success message and list of photo URLs.
    - HTTP status code.
    """
    photos = request.files.getlist("photos")
    bucket = buckit.get_bucket(config("GCLOUD_BUKIT"))
    photo_urls = []
    for i, photo in enumerate(photos):
        photo_bytes = io.BytesIO()
        photo.save(photo_bytes)
        photo_bytes.seek(0)
        blob_name = f"recipes/{recipe_id}/photo_{i}.jpg"
        blob = bucket.blob(blob_name)
        blob.upload_from_file(photo_bytes, content_type=photo.content_type)
        photo_urls.append(blob.public_url)

    doc_ref = db.collection("recipes").document(recipe_id)
    doc_ref.update({"photos": db.firestore.ArrayUnion(photo_urls)})
    return jsonify({"message": "Photos added successfully", "photos": photo_urls}), 200


@recipe.route("/recipe/<recipe_id>/photos", methods=["DELETE"])
@firebase_auth_required
def delete_photos(recipe_id):
    """
    Delete specific photos from a recipe.

    Expects form data containing:
    - photos: A list of photo URLs to be removed.

    Returns:
    - JSON response with a success message.
    - HTTP status code.
    """
    photos_to_remove = request.form.getlist("photos")
    bucket = buckit.get_bucket(config("GCLOUD_BUKIT"))

    for photo_url in photos_to_remove:
        photo_name = re.findall(r"([^/]+)/?$", photo_url)[0]
        blob = bucket.blob(f"recipes/{recipe_id}/{photo_name}")
        blob.delete()

    doc_ref = db.collection("recipes").document(recipe_id)
    doc = doc_ref.get()
    if doc.exists:
        doc_data = doc.to_dict()
        doc_data["photos"] = [
            photo for photo in doc_data["photos"] if photo not in photos_to_remove
        ]
        doc_ref.set(doc_data)
    else:
        print("No such document!")

    return jsonify({"message": "Photos removed successfully"}), 200


@recipe.route("/recipe/<string:document_id>/like", methods=["GET", "POST"])
@firebase_auth_required
def handle_like_recipe(document_id):
    """
    Handle like functionality for a given recipe.

    For GET:
    - Fetch like status for a recipe.

    For POST:
    - Expects a JSON payload with 'like' status (True/False) to update the like status.

    Returns:
    - JSON response with like status or a success message.
    - HTTP status code.
    """
    try:
        if request.method == "GET":
            doc_ref = db.collection("likes").document(document_id)
            doc = doc_ref.get()
            if doc.exists:
                recipe_data = doc.to_dict()
                likes = recipe_data.get("likes", [])
                return jsonify({"likes": likes}), 200
            else:
                return jsonify({"message": "Recipe not found"}), 404

        if request.method == "POST":
            user_id = g.user.get("user_id")
            like_status = request.json.get("like")
            if like_status is None:
                return jsonify({"error": "Invalid request"}), 400

            doc_ref = db.collection("likes").document(document_id)
            doc = doc_ref.get()
            if doc.exists:
                recipe_data = doc.to_dict()
                likes = recipe_data.get("likes", [])
                if like_status:
                    if user_id not in likes:
                        likes.append(user_id)
                else:
                    if user_id in likes:
                        likes.remove(user_id)

                # Update the 'likes' field in the recipe document
                doc_ref.update({"likes": likes})

                return jsonify({"message": "Like status updated successfully"}), 200
            else:
                # If the document doesn't exist, create a new "like" document
                doc_ref.set({"likes": [user_id] if like_status else []})
                return jsonify({"message": "Like status updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recipe.route("/recipe/search", methods=["POST"])
@firebase_auth_required
def search_recipe():
    """
    Search for recipes based on a given search term.

    Expects JSON payload containing:
    - search_term: The term to search for in recipe titles.

    Returns:
    - JSON response containing a list of matching recipes.
    - HTTP status code.
    """
    search_term = request.json["search_term"]
    recipes_ref = db.collection("recipes")

    query_ref = recipes_ref.where("title", ">=", search_term).where(
        "title", "<=", search_term + "\uf8ff"
    )

    results = []
    docs = query_ref.stream()
    for doc in docs:
        recipe = doc.to_dict()
        recipe["id"] = doc.id
        results.append(recipe)

    return jsonify(results), 200


@recipe.route("/recipe/<string:document_id>", methods=["PUT", "GET", "DELETE"])
@firebase_auth_required
def update_recipe(document_id):
    """
    Handle different operations on a single recipe.

    For DELETE:
    - Deletes the recipe with the given document_id.

    For GET:
    - Fetches the recipe with the given document_id.

    For PUT:
    - Updates the recipe with the given document_id.

    Returns:
    - JSON response with the operation result.
    - HTTP status code.
    """
    if request.method == "DELETE":
        try:
            doc_ref = db.collection("recipes").document(document_id)
            doc_ref.delete()
            bucket = buckit.get_bucket(config("GCLOUD_BUKIT"))
            blobs = bucket.list_blobs(prefix=f"recipes/{document_id}")
            bucket.delete_blobs(blobs)
            return jsonify({"message": "Recipe deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # For GET request
    if request.method == "GET":
        try:
            doc_ref = db.collection("recipes").document(document_id)
            doc = doc_ref.get()
            if doc.exists:
                recipe_data = doc.to_dict()
                return jsonify(recipe_data), 200
            else:
                return jsonify({"message": "Recipe not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    data = request.form
    dict_data = {}
    for key, value in data.lists():
        if "ingredients" in key:
            index = int(key.split("[")[1].split("]")[0])
            sub_key = key.split("[")[2].split("]")[0]
            if "ingredients" not in dict_data:
                dict_data["ingredients"] = []
            if len(dict_data["ingredients"]) - 1 < index:
                dict_data["ingredients"].append({})
            dict_data["ingredients"][index][sub_key] = value[0]
        elif "photos" not in key:
            dict_data[key] = value[0]

    # process form data and validate it here

    # retrieve the recipe document
    doc_ref = db.collection("recipes").document(document_id)

    # update the recipe document
    doc_ref.update(dict_data)

    return jsonify({"message": "Recipe updated successfully"}), 200
