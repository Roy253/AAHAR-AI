"""
AAHAR AI — Hostel Mess Nutrition Module

Features:
- Common Indian hostel-mess foods and approximate nutrient estimates per 100 g.
- Portion-based nutrition calculations.
- Daily nutrient-gap analysis.
- Practical, budget-aware add-on suggestions.
- Optional integration with the existing local Ollama client.

Important:
The built-in food values are approximate estimates for demonstration and
planning, not laboratory measurements. Recipes, oil, ingredients, and serving
sizes can change the actual values. Review and replace estimates with validated
data before using this module for health-critical decisions.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


NUTRIENTS = [
    "energy_kcal",
    "protein_g",
    "fiber_g",
    "carbs_g",
    "fat_g",
]

NUTRIENT_LABELS = {
    "energy_kcal": "Energy (kcal)",
    "protein_g": "Protein (g)",
    "fiber_g": "Fibre (g)",
    "carbs_g": "Carbohydrates (g)",
    "fat_g": "Fat (g)",
}

# Approximate values per 100 g of prepared food.
# Values vary significantly by recipe and preparation method.
HOSTEL_FOODS: list[dict[str, Any]] = [
    {"food_name": "Cooked white rice", "meal_types": ["Lunch", "Dinner"], "energy_kcal": 130, "protein_g": 2.7, "fiber_g": 0.4, "carbs_g": 28.2, "fat_g": 0.3, "category": "mess staple"},
    {"food_name": "Chapati / roti", "meal_types": ["Breakfast", "Lunch", "Dinner"], "energy_kcal": 297, "protein_g": 9.0, "fiber_g": 7.0, "carbs_g": 55.0, "fat_g": 3.7, "category": "mess staple"},
    {"food_name": "Plain dal", "meal_types": ["Lunch", "Dinner"], "energy_kcal": 100, "protein_g": 6.0, "fiber_g": 3.5, "carbs_g": 15.0, "fat_g": 2.0, "category": "protein source"},
    {"food_name": "Rajma curry", "meal_types": ["Lunch", "Dinner"], "energy_kcal": 125, "protein_g": 7.0, "fiber_g": 5.5, "carbs_g": 18.0, "fat_g": 2.5, "category": "protein source"},
    {"food_name": "Chole curry", "meal_types": ["Breakfast", "Lunch", "Dinner"], "energy_kcal": 160, "protein_g": 7.5, "fiber_g": 6.0, "carbs_g": 22.0, "fat_g": 5.0, "category": "protein source"},
    {"food_name": "Mixed vegetable sabzi", "meal_types": ["Lunch", "Dinner"], "energy_kcal": 100, "protein_g": 2.5, "fiber_g": 3.0, "carbs_g": 12.0, "fat_g": 4.5, "category": "vegetable"},
    {"food_name": "Aloo sabzi", "meal_types": ["Breakfast", "Lunch", "Dinner"], "energy_kcal": 120, "protein_g": 2.0, "fiber_g": 2.0, "carbs_g": 18.0, "fat_g": 4.0, "category": "vegetable"},
    {"food_name": "Plain curd", "meal_types": ["Breakfast", "Lunch", "Dinner", "Snacks"], "energy_kcal": 61, "protein_g": 3.5, "fiber_g": 0.0, "carbs_g": 4.7, "fat_g": 3.3, "category": "protein source"},
    {"food_name": "Milk", "meal_types": ["Breakfast", "Snacks"], "energy_kcal": 60, "protein_g": 3.2, "fiber_g": 0.0, "carbs_g": 4.8, "fat_g": 3.3, "category": "protein source"},
    {"food_name": "Poha", "meal_types": ["Breakfast", "Snacks"], "energy_kcal": 180, "protein_g": 3.5, "fiber_g": 2.0, "carbs_g": 30.0, "fat_g": 5.0, "category": "breakfast"},
    {"food_name": "Upma", "meal_types": ["Breakfast", "Snacks"], "energy_kcal": 150, "protein_g": 4.0, "fiber_g": 2.0, "carbs_g": 24.0, "fat_g": 4.0, "category": "breakfast"},
    {"food_name": "Idli", "meal_types": ["Breakfast", "Snacks"], "energy_kcal": 150, "protein_g": 4.5, "fiber_g": 2.0, "carbs_g": 30.0, "fat_g": 1.0, "category": "breakfast"},
    {"food_name": "Sambar", "meal_types": ["Breakfast", "Lunch", "Dinner"], "energy_kcal": 70, "protein_g": 3.0, "fiber_g": 3.0, "carbs_g": 10.0, "fat_g": 2.0, "category": "protein source"},
    {"food_name": "Vegetable khichdi", "meal_types": ["Lunch", "Dinner"], "energy_kcal": 125, "protein_g": 4.0, "fiber_g": 2.5, "carbs_g": 22.0, "fat_g": 2.5, "category": "meal"},
    {"food_name": "Banana", "meal_types": ["Breakfast", "Snacks"], "energy_kcal": 89, "protein_g": 1.1, "fiber_g": 2.6, "carbs_g": 22.8, "fat_g": 0.3, "category": "fruit"},
    {"food_name": "Apple", "meal_types": ["Breakfast", "Snacks"], "energy_kcal": 52, "protein_g": 0.3, "fiber_g": 2.4, "carbs_g": 13.8, "fat_g": 0.2, "category": "fruit"},
    {"food_name": "Roasted chana", "meal_types": ["Snacks"], "energy_kcal": 380, "protein_g": 20.0, "fiber_g": 10.0, "carbs_g": 58.0, "fat_g": 6.0, "category": "budget add-on"},
    {"food_name": "Peanuts", "meal_types": ["Snacks"], "energy_kcal": 567, "protein_g": 25.8, "fiber_g": 8.5, "carbs_g": 16.1, "fat_g": 49.2, "category": "budget add-on"},
    {"food_name": "Soy chunks, cooked", "meal_types": ["Lunch", "Dinner", "Snacks"], "energy_kcal": 160, "protein_g": 16.0, "fiber_g": 4.0, "carbs_g": 10.0, "fat_g": 5.0, "category": "budget add-on"},
    {"food_name": "Boiled egg", "meal_types": ["Breakfast", "Snacks"], "energy_kcal": 155, "protein_g": 13.0, "fiber_g": 0.0, "carbs_g": 1.1, "fat_g": 11.0, "category": "non-vegetarian add-on"},
]

DEFAULT_TARGETS = {
    "energy_kcal": 2000.0,
    "protein_g": 60.0,
    "fiber_g": 30.0,
    "carbs_g": 270.0,
    "fat_g": 70.0,
}

# Relative cost tiers are planning hints, not current market prices.
ADD_ONS = [
    {"food_name": "Roasted chana", "cost_tier": "low", "preferences": ["Vegetarian", "Vegetarian with eggs", "Non-vegetarian"], "best_for": ["protein_g", "fiber_g"]},
    {"food_name": "Banana", "cost_tier": "low", "preferences": ["Vegetarian", "Vegetarian with eggs", "Non-vegetarian"], "best_for": ["energy_kcal", "fiber_g"]},
    {"food_name": "Plain curd", "cost_tier": "low_to_medium", "preferences": ["Vegetarian", "Vegetarian with eggs", "Non-vegetarian"], "best_for": ["protein_g"]},
    {"food_name": "Milk", "cost_tier": "low_to_medium", "preferences": ["Vegetarian", "Vegetarian with eggs", "Non-vegetarian"], "best_for": ["protein_g", "energy_kcal"]},
    {"food_name": "Peanuts", "cost_tier": "low", "preferences": ["Vegetarian", "Vegetarian with eggs", "Non-vegetarian"], "best_for": ["protein_g", "energy_kcal"]},
    {"food_name": "Soy chunks, cooked", "cost_tier": "low", "preferences": ["Vegetarian", "Vegetarian with eggs", "Non-vegetarian"], "best_for": ["protein_g"]},
    {"food_name": "Boiled egg", "cost_tier": "low_to_medium", "preferences": ["Vegetarian with eggs", "Non-vegetarian"], "best_for": ["protein_g"]},
]


def food_database() -> pd.DataFrame:
    """Return the built-in hostel food list as a DataFrame."""
    return pd.DataFrame(HOSTEL_FOODS).copy()


def search_hostel_foods(query: str = "", meal_type: str | None = None) -> pd.DataFrame:
    """Search common mess foods, optionally filtering by meal type."""
    foods = food_database()
    query = (query or "").strip().casefold()

    if query:
        foods = foods[foods["food_name"].str.casefold().str.contains(query, regex=False)]

    if meal_type and meal_type != "All":
        foods = foods[foods["meal_types"].apply(lambda meals: meal_type in meals)]

    return foods.reset_index(drop=True)


def calculate_food_nutrition(food_name: str, portion_g: float) -> dict[str, Any]:
    """Calculate estimated nutrients for a food portion."""
    if portion_g <= 0:
        raise ValueError("Portion must be greater than zero.")

    matches = food_database()
    matches = matches[matches["food_name"].str.casefold() == food_name.strip().casefold()]
    if matches.empty:
        raise ValueError(f"Food not found in the hostel food list: {food_name}")

    food = matches.iloc[0]
    multiplier = float(portion_g) / 100.0

    result: dict[str, Any] = {
        "food_name": str(food["food_name"]),
        "portion_g": float(portion_g),
        "source": "AAHAR built-in approximate estimate",
    }
    for nutrient in NUTRIENTS:
        result[nutrient] = round(float(food[nutrient]) * multiplier, 2)

    return result


def calculate_daily_totals(meal_plan: list[dict[str, Any]]) -> dict[str, float]:
    """
    Calculate total estimated intake from meal-plan entries.

    Each entry must contain food_name and portion_g.
    Example:
        [{"food_name": "Plain dal", "portion_g": 180}, ...]
    """
    totals = {nutrient: 0.0 for nutrient in NUTRIENTS}

    for item in meal_plan:
        nutrition = calculate_food_nutrition(
            str(item["food_name"]),
            float(item["portion_g"]),
        )
        for nutrient in NUTRIENTS:
            totals[nutrient] += nutrition[nutrient]

    return {nutrient: round(value, 2) for nutrient, value in totals.items()}


def analyze_nutrition_gaps(
    daily_totals: dict[str, float],
    targets: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Compare logged intake with targets and show remaining amounts."""
    targets = targets or DEFAULT_TARGETS
    rows = []

    for nutrient in NUTRIENTS:
        target = float(targets[nutrient])
        consumed = float(daily_totals.get(nutrient, 0.0))
        remaining = max(target - consumed, 0.0)
        rows.append({
            "nutrient": NUTRIENT_LABELS[nutrient],
            "consumed": round(consumed, 2),
            "target": round(target, 2),
            "remaining": round(remaining, 2),
            "progress_pct": round(consumed / target * 100, 1) if target > 0 else None,
        })

    return pd.DataFrame(rows)


def recommend_budget_add_ons(
    daily_totals: dict[str, float],
    targets: dict[str, float] | None = None,
    food_preference: str = "Vegetarian",
    foods_to_avoid: list[str] | None = None,
    max_recommendations: int = 5,
) -> pd.DataFrame:
    """
    Rank practical add-ons based on gaps in protein, fibre, and energy.
    Cost tiers are relative only; no rupee prices are assumed.
    """
    targets = targets or DEFAULT_TARGETS
    foods_to_avoid = [food.strip().casefold() for food in (foods_to_avoid or []) if food.strip()]

    gaps = {
        nutrient: max(float(targets[nutrient]) - float(daily_totals.get(nutrient, 0)), 0)
        for nutrient in ("protein_g", "fiber_g", "energy_kcal")
    }
    weights = {"protein_g": 0.5, "fiber_g": 0.3, "energy_kcal": 0.2}

    rows = []
    for add_on in ADD_ONS:
        if food_preference not in add_on["preferences"]:
            continue
        if any(term in add_on["food_name"].casefold() for term in foods_to_avoid):
            continue

        food = next((x for x in HOSTEL_FOODS if x["food_name"] == add_on["food_name"]), None)
        if not food:
            continue

        # Use a 30 g snack portion, except milk/curd/soy/egg use practical portions.
        portion = {
            "Roasted chana": 30,
            "Banana": 100,
            "Plain curd": 150,
            "Milk": 200,
            "Peanuts": 20,
            "Soy chunks, cooked": 100,
            "Boiled egg": 50,
        }[add_on["food_name"]]

        score = 0.0
        for nutrient, weight in weights.items():
            target = max(float(targets.get(nutrient, 0)), 1.0)
            contribution = float(food[nutrient]) * portion / 100.0
            score += weight * min(contribution / target, 1.0) * (1.0 if gaps[nutrient] > 0 else 0.1)

        rows.append({
            "food_name": add_on["food_name"],
            "suggested_portion_g": portion,
            "cost_tier": add_on["cost_tier"],
            "protein_g": round(float(food["protein_g"]) * portion / 100.0, 2),
            "fiber_g": round(float(food["fiber_g"]) * portion / 100.0, 2),
            "energy_kcal": round(float(food["energy_kcal"]) * portion / 100.0, 2),
            "recommendation_score": round(score, 4),
            "reason": "May help address one or more nutrition gaps; confirm affordability and suitability.",
        })

    if not rows:
        return pd.DataFrame(columns=[
            "food_name", "suggested_portion_g", "cost_tier",
            "protein_g", "fiber_g", "energy_kcal",
            "recommendation_score", "reason",
        ])

    return pd.DataFrame(rows).sort_values(
        "recommendation_score", ascending=False
    ).head(max_recommendations).reset_index(drop=True)


def build_hostel_ai_prompt(
    question: str,
    meal_plan: list[dict[str, Any]],
    daily_totals: dict[str, float],
    targets: dict[str, float] | None = None,
    food_preference: str = "Vegetarian",
    budget_amount: float | None = None,
    budget_period: str = "Month",
    foods_to_avoid: list[str] | None = None,
) -> str:
    """Build a context-rich prompt for the existing local Ollama client."""
    targets = targets or DEFAULT_TARGETS
    foods_to_avoid = foods_to_avoid or []

    gaps = analyze_nutrition_gaps(daily_totals, targets).to_dict(orient="records")
    recommendations = recommend_budget_add_ons(
        daily_totals=daily_totals,
        targets=targets,
        food_preference=food_preference,
        foods_to_avoid=foods_to_avoid,
        max_recommendations=5,
    ).to_dict(orient="records")

    budget_text = (
        f"₹{budget_amount:.0f} per {budget_period}"
        if budget_amount is not None
        else "Not provided"
    )

    return f"""
You are AAHAR AI, a practical nutrition assistant for an Indian college hostel student.
The student mainly eats hostel mess food, which may have limited variety or protein.
Help improve existing meals with realistic, affordable additions instead of proposing
an expensive ideal diet.

FOOD PREFERENCE: {food_preference}
FOODS / ALLERGIES TO AVOID: {foods_to_avoid or "Not provided"}
EXTRA FOOD BUDGET: {budget_text}
LOGGED MEALS: {meal_plan}
CALCULATED DAILY TOTALS (approximate): {daily_totals}
TARGETS (illustrative defaults, not personalized medical advice): {targets}
NUTRIENT GAP TABLE: {gaps}
PRACTICAL ADD-ON CANDIDATES: {recommendations}

USER QUESTION: {question}

RULES:
- Give practical advice using common hostel foods: rice, roti, dal, sabzi, curd,
  rajma, chole, poha, idli, sambar, and affordable add-ons such as roasted chana,
  peanuts, milk, curd, or soy chunks where suitable.
- Prefer improving the mess plate first (for example, add a serving of dal or curd)
  before recommending extra purchases.
- Do not invent current prices, rupee costs, food availability, or exact nutrient values.
- The built-in food nutrient values are approximate estimates and depend on recipes.
- Do not recommend any foods listed in the avoid list. For allergies, remind the user
  to check ingredients and cross-contamination.
- Never diagnose, promise treatment, or claim a food cures a medical condition.
- Be concise, supportive, and realistic for a student budget.
- If meal logs are incomplete, clearly state that the analysis is based only on logged foods.
"""


def ask_hostel_ai(
    question: str,
    meal_plan: list[dict[str, Any]],
    daily_totals: dict[str, float],
    targets: dict[str, float] | None = None,
    food_preference: str = "Vegetarian",
    budget_amount: float | None = None,
    budget_period: str = "Month",
    foods_to_avoid: list[str] | None = None,
) -> str:
    """
    Call the existing src.ollama_client.ask_ollama function.

    Import is inside the function so the rest of this module can be used even
    if Ollama is not installed or configured yet.
    """
    from src.ollama_client import ask_ollama

    prompt = build_hostel_ai_prompt(
        question=question,
        meal_plan=meal_plan,
        daily_totals=daily_totals,
        targets=targets,
        food_preference=food_preference,
        budget_amount=budget_amount,
        budget_period=budget_period,
        foods_to_avoid=foods_to_avoid,
    )
    return ask_ollama(prompt)


if __name__ == "__main__":
    example_meals = [
        {"food_name": "Cooked white rice", "portion_g": 250},
        {"food_name": "Plain dal", "portion_g": 180},
        {"food_name": "Mixed vegetable sabzi", "portion_g": 100},
        {"food_name": "Chapati / roti", "portion_g": 80},
    ]
    totals = calculate_daily_totals(example_meals)

    print("Daily totals from example meals:")
    print(totals)
    print("\nNutrition gaps:")
    print(analyze_nutrition_gaps(totals).to_string(index=False))
    print("\nSuggested add-ons:")
    print(recommend_budget_add_ons(totals).to_string(index=False))
