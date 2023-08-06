import ast
import json
from flask import Blueprint, request, jsonify, g
from lib.iam import firebase_auth_required
from lib.macro import macro_calculator
from werkzeug.datastructures import FileStorage
import openai
import random
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
        num_to_sample = random.randint(0, len(pantry_items))
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

def store_gpt_recipe(recipe):
    recipe = json.loads(recipe)
    # get the form data and convert it to a dictionary
    form_data = dict(recipe)

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


    # creating a unique id for the recipe
    recipe_id = str(uuid.uuid4())

    bucket = buckit.get_bucket("prepr-391015.appspot.com")

    doc_ref = db.collection("recipes").document(recipe_id)

    doc_ref.set(
        {
            "author": "GPT Chef",
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": title,
            "instructions": instructions,
            "calories": calories,
            "fats": fats,
            "carbs": carbs,
            "proteins": proteins,
            "ingredients": ingredients,  # use the processed list of ingredients
            "photos": "",
        }
    )

    return jsonify({"message": "Recipe created successfully"}), 200



@main.route("/gen<days>", methods=["GET", "POST"])
@firebase_auth_required
def gen_meal_plan(days):
    days = int(days)  # convert days to integer
    meal_plan = []

    for i in range(days):
        recipe = json.loads(generate_recipe(), strict=False)
        meal_plan.append(recipe)
    return jsonify(meal_plan), 200

