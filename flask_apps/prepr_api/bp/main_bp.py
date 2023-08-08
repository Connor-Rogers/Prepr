import datetime, uuid
import json
from flask import Blueprint, request, jsonify, g
from lib.firebase import db
import datetime
import uuid

from lib.iam import firebase_auth_required
from lib.recpie_gen import generate_recipe

# Create a blueprint for the routes
main = Blueprint("main_bp", __name__)


@main.route("/")
def index():
    """Root endpoint to test the API."""
    return "Prepr API Beta"


@main.route("/gen<int:days>", methods=["GET", "POST"])
@firebase_auth_required
def gen_meal_plan(days):
    """
    Generate a meal plan for a specified number of days using the provided pantry items.

    :param days: Number of days for which the meal plan is generated.
    :return: A JSON object containing recipes for each day.
    """
    pantry_items = []
    try:
        data = request.get_json()
        pantry_items = data.get("pantryItems", None)
    except:
        pantry_items = None

    meal_plan = {}
    for day in range(days):
        recipe = {}
        retries = 0
        cond = True
        while cond:
            try:
                # Generate a recipe using the pantry items and the user ID
                recipe = generate_recipe(pantry_items, g.user.get("user_id"))
                # Try to parse the recipe string as JSON
                recipe = json.loads(recipe, strict=False)
                cond = False
            except json.decoder.JSONDecodeError:
                # Handle JSON decoding errors and retry
                retries = retries + 1
                if retries > 3:
                    cond = False

        meal_plan[day] = recipe
    return jsonify(meal_plan), 200


@main.route("/gen/add", methods=["POST"])
@firebase_auth_required
def add_generated_recipe():
    """
    Add a generated recipe to the database.

    :return: A JSON object containing a message and the ID of the created recipe.
    """
    # Get the form data and convert it to a dictionary
    form_data = request.json

    # Extract values directly from the provided data
    title = form_data.get("title")
    instructions = form_data.get("instructions")
    calories = form_data.get("calories")
    fats = form_data.get("fats")
    carbs = form_data.get("carbs")
    proteins = form_data.get("proteins")
    ingredients = form_data.get(
        "ingredients", []
    )  # Directly extract the ingredients list

    # Create a unique ID for the recipe
    recipe_id = str(uuid.uuid4())
    doc_ref = db.collection("recipes").document(recipe_id)

    # Set the recipe document with the provided details
    doc_ref.set(
        {
            "author": g.user.get(
                "user_id"
            ),  # Setting the user_id from the logged in user
            "date": datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),  # Current timestamp
            "title": title,
            "instructions": instructions,
            "calories": calories,
            "fats": fats,
            "carbs": carbs,
            "proteins": proteins,
            "ingredients": ingredients,  # Use the provided list of ingredients
        }
    )

    return (
        jsonify({"message": "Recipe created successfully", "recipe_id": recipe_id}),
        200,
    )
