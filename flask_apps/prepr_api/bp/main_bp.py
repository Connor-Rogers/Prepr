import ast
import json
from flask import Blueprint, request, jsonify, g
from lib.iam import firebase_auth_required
from lib.macro import macro_calculator
from werkzeug.datastructures import FileStorage
import openai
import random
from lib.firebase import buckit, db

main = Blueprint("main_bp", __name__)


@main.route("/")
def index():
    return "Hello World!"

def get_random_recipe_from_likes(user_id):
    likes_ref = db.collection("likes").document(user_id)
    likes_doc = likes_ref.get()

    # If the document doesn't exist, create a new dictionary. Otherwise, get the data from the existing document
    likes = likes_doc.to_dict() if likes_doc.exists else {}

    random_liked = random.choice(likes)
    return random_liked

def get_random_recipe():
    # Fetch all recipes
    recipes_ref = db.collection("recipes")
    docs = recipes_ref.get()

    # Convert all recipes to a list
    recipes = [doc.to_dict() for doc in docs]

    # Choose a random recipe
    random_recipe = random.choice(recipes)
    return random_recipe

#add to recipe database button for when gpt makes a recipe
#Add back pantry items to prompts when included
#gen 3 recipes when page loads tiles for recipe will have name macros and pics
#upgrade css


def generate_recipe():
    openai.api_key = "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"
    #if pantryItems != null: 

    data = request.get_json()
    pantry_items = data.get("pantryItems")
    if pantry_items:
        num_to_sample = len(pantry_items)%3
        if num_to_sample == 0: num_to_sample = 1
        num_items = min(random.randint(1, num_to_sample), len(pantry_items))
        items_for_day = random.sample(pantry_items, num_items)
        pantry_items = [item for item in pantry_items if item not in items_for_day]
    prompt = (
        """Please generate a detailed recipe including the title, ingredients, instructions, and macro nutritional information. Use the following recipe as a template and inspiration """
        + str(get_random_recipe_from_likes())
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
    print(prompt)
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
    print (prompt)
    print(recipe)
    return recipe


@main.route("/gen<days>", methods=["GET", "POST"])
# @firebase_auth_required
def gen_meal_plan(days):
    days = 1
    meal_plan = {}

    for i in range(days):
        meal_plan = json.loads(generate_recipe(), strict=False)
    return jsonify(meal_plan), 200
