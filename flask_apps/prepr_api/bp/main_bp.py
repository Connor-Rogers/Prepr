from flask import Blueprint, request, jsonify, g
from lib.iam import firebase_auth_required
from lib.macro import macro_calculator
from werkzeug.datastructures import FileStorage
import openai

main = Blueprint("main_bp", __name__)


@main.route("/")
def index():
    return "Hello World!"


def generate_recipe():
    openai.api_key = "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"

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="""Please generate a detailed recipe including the title, ingredients, instructions, and macro nutritional information.
        The recipe should be formatted as follows:
        Title: The name of the dish
        Ingredients:
        - Ingredient 1
        - Ingredient 2
        - Ingredient 3
        - ...
        Instructions:
        1. First instruction
        2. Second instruction
        3. ...
        Macros:
        Calories: X kcal
        Protein: Y g
        Carbs: Z g
        Fat: W g
        """,
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
    days = int(days)
    meal_plan = {}

    for i in range(days):
        meal_plan[f"Day {i+1}"] = generate_recipe()

    return jsonify(meal_plan)
