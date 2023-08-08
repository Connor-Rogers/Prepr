import datetime, uuid
import json
from flask import Blueprint, request, jsonify, g
from lib.firebase import db
import datetime
import uuid

from lib.iam import firebase_auth_required
from lib.recpie_gen import generate_recipe

main = Blueprint("main_bp", __name__)


@main.route("/")
def index():
    return "Prepr API Beta"


@main.route("/gen<int:days>", methods=["GET", "POST"])
@firebase_auth_required
def gen_meal_plan(days):
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
                recipe = generate_recipe(pantry_items, g.user.get("user_id"))
                recipe = json.loads(recipe, strict=False)
                cond = False
            except json.decoder.JSONDecodeError:
                retries = retries + 1
                if retries > 3:
                    cond = False
                print("Failed To Generate Good Recipes")

        meal_plan[day] = recipe
    print(meal_plan)
    return jsonify(meal_plan), 200


@main.route("/gen/add", methods=["POST"])
@firebase_auth_required
def add_generated_recipe():
    # get the form data and convert it to a dictionary
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

    # creating a unique id for the recipe
    recipe_id = str(uuid.uuid4())
    doc_ref = db.collection("recipes").document(recipe_id)

    doc_ref.set(
        {
            "author": g.user.get("user_id"),  # setting user_id as a constant
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": title,
            "instructions": instructions,
            "calories": calories,
            "fats": fats,
            "carbs": carbs,
            "proteins": proteins,
            "ingredients": ingredients,  # Directly use the provided list of ingredients
        }
    )

    return (
        jsonify({"message": "Recipe created successfully", "recipe_id": recipe_id}),
        200,
    )
