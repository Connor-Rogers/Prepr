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


def get_random_recipe():
    # Fetch all recipes
    recipes_ref = db.collection("recipes")
    docs = recipes_ref.get()

    # Convert all recipes to a list
    recipes = [doc.to_dict() for doc in docs]

    # Choose a random recipe
    random_recipe = random.choice(recipes)
    return random_recipe


def generate_recipe():
    openai.api_key = "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"
    prompt = (
        """Please generate a detailed recipe including the title, ingredients, instructions, and macro nutritional information. Use the following recipe as a template """
        + str(get_random_recipe())
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
