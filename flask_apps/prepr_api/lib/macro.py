def macro_calculator(
    height_ft: str,
    height_in: str,
    weight: int,
    age: int,
    activity: str,
    gender: str,
    goal: str,
):
    """
    Calculate macronutrient needs based on user details and goals.

    Parameters:
    - height_ft (str): User's height in feet.
    - height_in (str): User's height in inches. This is an additional measurement to the height in feet.
    - weight (int): User's weight in pounds.
    - age (int): User's age in years.
    - activity (str): User's level of physical activity. Acceptable values are: 'sedentary', 'light', 'moderate', 'active', 'very active'.
    - gender (str): User's gender. Acceptable values are: 'male', 'female', and any other value will be considered as 'other'.
    - goal (str): User's fitness goal. Acceptable values are: 'lose' (to lose weight) and 'gain' (to gain weight).

    Returns:
    - dict: A dictionary containing the daily macronutrient needs in grams for carbohydrates, protein, and fat.
    """
    body_mass_ratio = 0
    total_daily_energy = 0
    weight_in_kg = weight / 2.20462
    height_in_cm = ((height_ft * 12) + height_in) * 2.54

    # Calculate BMR
    if gender == "male":
        body_mass_ratio = 10 * weight_in_kg + 6.25 * height_in_cm - 5 * age + 5
    elif gender == "female":
        body_mass_ratio = 10 * weight_in_kg + 6.25 * height_in_cm - 5 * age - 161
    else:
        body_mass_ratio = 10 * weight_in_kg + 6.25 * height_in_cm - 5 * age - 78

    # Calculate TDEE
    if activity == "sedentary":
        total_daily_energy = body_mass_ratio * 1.2
    elif activity == "light":
        total_daily_energy = body_mass_ratio * 1.375
    elif activity == "moderate":
        total_daily_energy = body_mass_ratio * 1.55
    elif activity == "active":
        total_daily_energy = body_mass_ratio * 1.725
    elif activity == "very active":
        total_daily_energy = body_mass_ratio * 1.9
    else:
        total_daily_energy = body_mass_ratio * 1.2
    if goal == "lose":
        total_daily_energy -= 500
    elif goal == "gain":
        total_daily_energy += 500

    # Calculate macros
    return {
        "carbs": int(0.5 * total_daily_energy / 4),
        "protein": int(0.25 * total_daily_energy / 4),
        "fat": int(0.25 * total_daily_energy / 9),
    }
