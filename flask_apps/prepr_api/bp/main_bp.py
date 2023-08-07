import datetime, uuid
import json
from flask import Blueprint, request, jsonify, g
from lib.iam import firebase_auth_required
from lib.macro import macro_calculator
from werkzeug.datastructures import FileStorage
import openai
import random
import ast
from lib.firebase import buckit, db
from datetime import timedelta
import io, re
import datetime
import uuid

main = Blueprint("main_bp", __name__)


@main.route("/")
def index():
    return "Hello World!"


def get_random_recipe_from_likes(user_id):
    # Find recipes liked by the user
    liked_recipes = []
    likes_docs = db.collection("likes").stream()

    for doc in likes_docs:
        likes = doc.to_dict().get("likes", [])
        if user_id in likes:
            liked_recipes.append(doc.id)

    # If the user has liked any recipes, pick one at random
    if liked_recipes:
        random_recipe_id = random.choice(liked_recipes)
    else:
        # If user hasn't liked any recipe, pick a random recipe from all recipes
        all_recipe_ids = [doc.id for doc in db.collection("recipes").stream()]
        if not all_recipe_ids:
            return {}  # Return empty dict if there are no recipes in the database
        random_recipe_id = random.choice(all_recipe_ids)

    # Get the recipe details from the "recipes" collection
    recipe_doc = db.collection("recipes").document(random_recipe_id).get()
    if recipe_doc.exists:
        return recipe_doc.to_dict()
    return {}


# add to recipe database button for when gpt makes a recipe
# Add back pantry items to prompts when included
# gen 3 recipes when page loads tiles for recipe will have name macros and pics
# upgrade css


def generate_recipe(pantry_items: list = None, user_id=str):
    openai.api_key = "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"
    # if pantryItems != null:
    items_for_day = []
    if pantry_items:
        num_to_sample = random.randint(0, len(pantry_items))
        if num_to_sample == 0:
            num_to_sample = 1
        num_items = min(random.randint(1, num_to_sample), len(pantry_items))
        items_for_day = random.sample(pantry_items, num_items)
        pantry_items = [item for item in pantry_items if item not in items_for_day]
        prompt = (
            """Please generate a detailed recipe including the title, ingredients, instructions, and macro nutritional information. Use the following recipe as a template and inspiration """
            + str(get_random_recipe_from_likes(user_id))
            + """ incorporate the following additional ingredients into the recipe """
            + str(items_for_day)
            + """ and should be formated as a json with the following feilds: 
    title: "title of recipe"
    ingredients: [{"ingredient": "ingredient name", "quantity": "quantity unit"}, {"ingredient": "ingredient name", "quantity": "quantity unit"}]] 
    instructions: "Instructions for recipe"
    calories: "calories"`
    fats: "fats"
    carbs: "carbs"
    proteins: "proteins"
    """
        )
    else:
        prompt = (
            """Please generate a detailed recipe including the title, ingredients, instructions, and macro nutritional information. Use the following recipe as a template and inspiration """
            + str(get_random_recipe_from_likes())
            + """ and should be formated as a json with the following feilds: 
    title: "title of recipe"
    ingredients: [{"ingredient": "ingredient name", "quantity": "quantity unit"}, {"ingredient": "ingredient name", "quantity": "quantity unit"}]] 
    instructions: "Instructions for recipe"
    calories: "calories"`
    fats: "fats"
    carbs: "carbs"
    proteins: "proteins"
    """
        )

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.3,
        max_tokens=600,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    recipe = response.choices[0].text.strip()
    return recipe


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
        while True:
            try:
                recipe = generate_recipe(pantry_items, g.user.get("user_id"))
                recipe = json.loads(recipe, strict=False)
                break
            except json.decoder.JSONDecodeError:
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
            "author": "U4KM71XEAOeIuWCb7S0s",  # setting user_id as a constant
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
