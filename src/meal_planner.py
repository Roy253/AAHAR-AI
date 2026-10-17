
from pathlib import Path

import pandas as pd


# ============================================================
# AAHAR AI — DAILY MEAL PLANNER
# ============================================================

DATA_PATH = Path("data/processed/ifct_foods_clean.csv")

MEALS = [
    "Breakfast",
    "Lunch",
    "Snacks",
    "Dinner",
]

NUTRIENT_COLUMNS = {
    "protein_g": "Protein (g)",
    "fiber_total_g": "Dietary fibre (g)",
    "carbs_available_g": "Carbohydrates (g)",
    "fat_g": "Fat (g)",
    "energy_kj": "Energy (kJ)",
}

FOOD_COLUMNS = [
    "food_code",
    "food_name",
    *NUTRIENT_COLUMNS.keys(),
]


def load_foods():
    """Load the cleaned IFCT food dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}. "
            "Run src.preprocess first."
        )

    foods = pd.read_csv(DATA_PATH)

    missing_columns = [
        column
        for column in FOOD_COLUMNS
        if column not in foods.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Dataset is missing required columns: {missing_columns}"
        )

    for column in NUTRIENT_COLUMNS:
        foods[column] = pd.to_numeric(
            foods[column],
            errors="coerce",
        )

    foods["food_code"] = foods["food_code"].astype(str).str.strip()
    foods["food_name"] = foods["food_name"].astype(str).str.strip()

    foods = foods.drop_duplicates(
        subset=["food_code"],
        keep="first",
    )

    return foods[FOOD_COLUMNS].reset_index(drop=True)


def calculate_food_nutrition(food, quantity_g):
    """
    Calculate nutrient contributions for a quantity of food.

    IFCT values are assumed to be per 100 g.
    Missing source nutrients remain missing, not zero.
    """
    if quantity_g <= 0:
        raise ValueError("Food quantity must be greater than zero.")

    multiplier = quantity_g / 100.0

    result = {
        "food_code": food["food_code"],
        "food_name": food["food_name"],
        "quantity_g": float(quantity_g),
    }

    for column in NUTRIENT_COLUMNS:
        value = pd.to_numeric(
            pd.Series([food[column]]),
            errors="coerce",
        ).iloc[0]

        result[column] = (
            float(value) * multiplier
            if pd.notna(value)
            else float("nan")
        )

    return result


def calculate_meal_nutrition(items):
    """
    Calculate nutrient totals for one meal.

    items: list of dictionaries containing food_code and quantity_g.
    """
    foods = load_foods()
    calculated_items = []

    for item in items:
        food_code = str(item["food_code"]).strip()
        quantity_g = float(item["quantity_g"])

        matches = foods[foods["food_code"] == food_code]

        if matches.empty:
            raise ValueError(
                f"Food code '{food_code}' was not found in the dataset."
            )

        food = matches.iloc[0]

        calculated_items.append(
            calculate_food_nutrition(food, quantity_g)
        )

    item_columns = [
        "food_code",
        "food_name",
        "quantity_g",
        *NUTRIENT_COLUMNS.keys(),
    ]

    item_df = pd.DataFrame(
        calculated_items,
        columns=item_columns,
    )

    totals = {
        column: (
            item_df[column].sum(min_count=1)
            if not item_df.empty
            else 0.0
        )
        for column in NUTRIENT_COLUMNS
    }

    return {
        "items": item_df,
        "totals": totals,
    }


def calculate_daily_nutrition(day_plan):
    """
    Calculate meal-wise and full-day nutrition.

    day_plan example:
    {
        "Breakfast": [
            {"food_code": "H012", "quantity_g": 30}
        ],
        "Lunch": [
            {"food_code": "H008", "quantity_g": 50}
        ],
        "Snacks": [],
        "Dinner": []
    }
    """
    meal_results = {}
    daily_totals = {
        column: 0.0
        for column in NUTRIENT_COLUMNS
    }

    for meal in MEALS:
        items = day_plan.get(meal, [])

        result = calculate_meal_nutrition(items)
        meal_results[meal] = result

        for column in NUTRIENT_COLUMNS:
            value = result["totals"][column]

            if pd.notna(value):
                daily_totals[column] += value

    return {
        "meals": meal_results,
        "daily_totals": daily_totals,
    }


def get_available_foods():
    """Return food codes and names for selecting meal ingredients."""
    return load_foods()[["food_code", "food_name"]]


if __name__ == "__main__":
    foods = load_foods()

    if foods.empty:
        raise ValueError("The cleaned food dataset contains no records.")

    # Small demonstration using the first food in the real dataset.
    sample = foods.iloc[0]

    demo_plan = {
        "Breakfast": [
            {
                "food_code": sample["food_code"],
                "quantity_g": 50,
            }
        ],
        "Lunch": [],
        "Snacks": [],
        "Dinner": [],
    }

    result = calculate_daily_nutrition(demo_plan)

    print("AAHAR AI — MEAL PLANNER TEST")
    print("=" * 45)
    print(f"Sample food: {sample['food_name']} (50 g)")

    print("\nBreakfast nutrition:")
    for column, label in NUTRIENT_COLUMNS.items():
        value = result["meals"]["Breakfast"]["totals"][column]
        print(
            f"{label}: "
            f"{value:.2f}" if pd.notna(value)
            else f"{label}: Missing in source"
        )

    print("\nFull-day nutrition:")
    for column, label in NUTRIENT_COLUMNS.items():
        value = result["daily_totals"][column]
        print(
            f"{label}: {value:.2f}" if pd.notna(value)
            else f"{label}: Missing in source"
        )
