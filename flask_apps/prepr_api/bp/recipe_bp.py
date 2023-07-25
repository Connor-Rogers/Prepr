from flask import Blueprint, request, jsonify, g
from lib.iam import firebase_auth_required
from lib.firebase import buckit, db
from PIL import Image
from datetime import timedelta
import io, re
import datetime
import uuid


recipe = Blueprint("recipe_bp", __name__)


@recipe.route("/recipe/create", methods=["POST"])
@firebase_auth_required
def create_recipe():
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

    # print the list of ingredients
    print(ingredients)

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

    bucket = buckit.get_bucket("prepr-391015.appspot.com")
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

    return jsonify({"message": "Recipe created successfully"}), 200


@recipe.route("/recipe/<string:document_id>/photos", methods=["GET"])
@firebase_auth_required
def get_recipe_photos(document_id):
    doc_ref = db.collection("recipes").document(document_id)
    try:
        doc = doc_ref.get()
        if doc.exists:
            profile_data = doc.to_dict()

            # Fetch the image url from Firebase storage
            bucket = buckit.get_bucket("prepr-391015.appspot.com")

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


@recipe.route("/recipe/<string:document_id>", methods=["GET", "DELETE"])
def handle_recipe(document_id):
    if request.method == "DELETE":
        try:
            doc_ref = db.collection("recipes").document(document_id)
            doc_ref.delete()
            bucket = buckit.get_bucket("prepr-391015.appspot.com")
            blobs = bucket.list_blobs(prefix=f"recipes/{document_id}")
            bucket.delete_blobs(blobs)
            return jsonify({"message": "Recipe deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # For GET request
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


@recipe.route("/recipe/<recipe_id>", methods=["PUT"])
@firebase_auth_required
def update_recipe(recipe_id):
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
    doc_ref = db.collection("recipes").document(recipe_id)

    # update the recipe document
    doc_ref.update(dict_data)

    return jsonify({"message": "Recipe updated successfully"}), 200


@recipe.route("/recipe/<recipe_id>/photos", methods=["POST"])
@firebase_auth_required
def add_photos(recipe_id):
    photos = request.files.getlist("photos")
    bucket = buckit.get_bucket("prepr-391015.appspot.com")
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
    photos_to_remove = request.form.getlist("photos")
    bucket = buckit.get_bucket("prepr-391015.appspot.com")

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


# except Exception as e:
# return jsonify({"error": str(e)}), 500
