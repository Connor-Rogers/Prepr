from flask import Blueprint, request, jsonify
from lib.iam import firebase_auth_required
from lib.firebase import db

meal_plan = Blueprint("planner_bp", __name__)


@meal_plan.route("/meal_plan/<string:user_id>/day/<int:day_number>", methods=["PUT"])
@firebase_auth_required
def handle_day_meal_plan(user_id, day_number):
    """
    Update the number of meals planned for a specific day for a user.

    :param user_id: The unique ID of the user.
    :param day_number: Day for which the meal plan needs to be updated.
    :return: A JSON response indicating the outcome.
    """
    try:
        # Assume the structure of meal_plan is {day: [meals]}
        meal_plan_ref = db.collection("meal_plan").document(user_id)
        meal_plan_doc = meal_plan_ref.get()

        # If the document doesn't exist, create a new dictionary. Otherwise, get the data from the existing document
        meal_plan = meal_plan_doc.to_dict() if meal_plan_doc.exists else {}

        # Convert day_number to string for use as a key.
        str_day_number = str(day_number)

        # Get the number of meals from the request body
        request_data = request.get_json()
        num_meals = request_data.get("num_meals", 7)  # Default to 7 meals

        # Ensure the number of meals is between 1 and 7
        num_meals = min(max(num_meals, 1), 7)

        # If there are already meals for the day, adjust the number of meals
        meal_plan[str_day_number] = (meal_plan.get(str_day_number, []) + [None] * 7)[
            :num_meals
        ]

        meal_plan_ref.set(meal_plan)

        return jsonify({"message": "Day meal plan updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@meal_plan.route("/meal_plan/<string:user_id>", methods=["GET"])
@firebase_auth_required
def get_meal_plan(user_id):
    """
    Retrieve the full meal plan for a user, with recipe details.

    :param user_id: The unique ID of the user.
    :return: A JSON response containing the meal plan with recipes or error details.
    """
    try:
        # Getting the user's meal plan from the Firestore
        meal_plan_ref = db.collection("meal_plan").document(user_id)
        meal_plan_doc = meal_plan_ref.get()

        # If the meal plan doesn't exist, initialize it as an empty object
        if not meal_plan_doc.exists:
            return jsonify({}), 200

        meal_plan = meal_plan_doc.to_dict()

        # If the meal plan exists but is empty, return an empty object
        if not meal_plan:
            return jsonify({}), 200

        # Define a placeholder recipe
        placeholder_recipe = {
            "title": "No recipe selected",
            "calories": 0,
            "carbs": 0,
            "fats": 0,
            "proteins": 0,
            "photos": [],
        }

        # Fetch the recipes for the meal plan
        recipes_ref = db.collection("recipes")
        meal_plan_with_recipes = {}
        for day, recipe_ids in meal_plan.items():
            meal_plan_with_recipes[day] = [
                recipes_ref.document(id).get().to_dict() if id else placeholder_recipe
                for id in recipe_ids
            ]

            # Limit the fields returned for each recipe
            for i in range(len(meal_plan_with_recipes[day])):
                if (
                    meal_plan_with_recipes[day][i] is not placeholder_recipe
                ):  # Don't overwrite placeholder
                    meal_plan_with_recipes[day][i] = {
                        "id": recipe_ids[i],
                        "title": meal_plan_with_recipes[day][i]["title"],
                        "calories": meal_plan_with_recipes[day][i]["calories"],
                        "carbs": meal_plan_with_recipes[day][i]["carbs"],
                        "fats": meal_plan_with_recipes[day][i]["fats"],
                        "proteins": meal_plan_with_recipes[day][i]["proteins"],
                    }
        return jsonify(meal_plan_with_recipes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@meal_plan.route(
    "/meal_plan/<string:user_id>/recipe/<string:recipe_id>", methods=["POST"]
)
@firebase_auth_required
def add_to_meal_plan(user_id, recipe_id):
    """
    Add a specific recipe to the user's meal plan. If there's an available slot in the plan, the recipe is added.
    Otherwise, the last recipe of the most filled day is replaced.

    :param user_id: The unique ID of the user.
    :param recipe_id: The unique ID of the recipe to be added.
    :return: A JSON response indicating the outcome.
    """
    try:
        # Getting the user's meal plan from the Firestore
        meal_plan_ref = db.collection("meal_plan").document(user_id)
        meal_plan_doc = meal_plan_ref.get()

        # If the meal plan doesn't exist, initialize it as an empty object
        if not meal_plan_doc.exists:
            meal_plan_ref.set({"recipes": []})  # Initialize a new document
            return jsonify({}), 200

        meal_plan = meal_plan_doc.to_dict()

        # If the meal plan exists but is empty, return an empty object
        if not meal_plan:
            return jsonify({}), 200
        # Get the data from the existing document
        meal_plan = meal_plan_doc.to_dict()

        # Add the recipe id to the meal plan
        for day in meal_plan:
            if None in meal_plan[day]:  # If there's an empty slot in this day
                meal_plan[day][
                    meal_plan[day].index(None)
                ] = recipe_id  # Replace the first empty slot with the recipe id
                break
        else:  # If all days are full
            # Check if there are more than 7 recipes
            total_recipes = sum(len(day_recipes) for day_recipes in meal_plan.values())
            if total_recipes >= 7:
                # If there are 7 or more recipes, replace the 7th recipe
                meal_plan[day][-1] = recipe_id
            else:
                # If there are less than 7 recipes, add the new recipe
                meal_plan[day].append(recipe_id)

        meal_plan_ref.set(meal_plan)

        return jsonify({"message": "Recipe added to meal plan successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@meal_plan.route(
    "/meal_plan/<string:user_id>/day/remove/<int:index>/<int:meal_index>",
    methods=["DELETE"],
)
@firebase_auth_required
def remove_meal_from_day(user_id, index, meal_index):
    """
    Remove a meal from a specific day in the user's meal plan.

    :param user_id: The unique ID of the user.
    :param index: Index of the day from which the meal needs to be removed.
    :param meal_index: Index of the meal to be removed on the specified day.
    :return: A JSON response indicating the outcome.
    """
    try:
        # Get the user's meal plan from the Firestore
        meal_plan_ref = db.collection("meal_plan").document(user_id)
        meal_plan_doc = meal_plan_ref.get()

        # If the meal plan doesn't exist or is empty, nothing to delete
        if not meal_plan_doc.exists:
            return jsonify({"message": "No meal plan found"}), 404

        meal_plan = meal_plan_doc.to_dict()

        # Convert the meal_plan keys to list and get the 'day_number' based on 'index'
        day_number = list(meal_plan.keys())[index]

        # If the day doesn't exist in the meal plan, or there are no meals for that day, nothing to delete
        if (
            str(day_number) not in meal_plan
            or len(meal_plan[str(day_number)]) <= meal_index
        ):
            return jsonify({"message": "No such meal in the plan"}), 404

        # Delete the meal at the specified index for the given day
        meal_plan[str(day_number)].pop(meal_index)

        # Save the updated meal plan
        meal_plan_ref.set(meal_plan)

        return jsonify({"message": "Meal removed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
