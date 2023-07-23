from flask import Blueprint, request, jsonify
from lib.iam import firebase_auth_required
from lib.firebase import buckit, db
from PIL import Image
import io, re
import openai
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
