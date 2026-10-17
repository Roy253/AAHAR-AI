
import math
import unittest

import pandas as pd

from src.meal_planner import (
    MEALS,
    load_foods,
    calculate_food_nutrition,
    calculate_meal_nutrition,
    calculate_daily_nutrition,
)


class TestMealPlanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load the real IFCT dataset for testing."""
        cls.foods = load_foods()

        if cls.foods.empty:
            raise AssertionError("The IFCT dataset is empty.")

        cls.food = cls.foods.iloc[0]
        cls.food_code = cls.food["food_code"]

    def test_dataset_loads(self):
        """Verify the dataset has food records and unique codes."""
        self.assertGreater(len(self.foods), 0)
        self.assertTrue(self.foods["food_code"].is_unique)
        self.assertIn("food_name", self.foods.columns)

    def test_100g_is_twice_50g(self):
        """Verify nutrient values scale with portion size."""
        food_50 = calculate_food_nutrition(self.food, 50)
        food_100 = calculate_food_nutrition(self.food, 100)

        nutrients = [
            "protein_g",
            "fiber_total_g",
            "carbs_available_g",
            "fat_g",
            "energy_kj",
        ]

        for nutrient in nutrients:
            value_50 = food_50[nutrient]
            value_100 = food_100[nutrient]

            if pd.isna(value_50):
                self.assertTrue(pd.isna(value_100))
            else:
                self.assertTrue(
                    math.isclose(
                        value_100,
                        value_50 * 2,
                        rel_tol=1e-9,
                    ),
                    f"Incorrect scaling for {nutrient}",
                )

    def test_invalid_quantities(self):
        """Zero and negative portions must be rejected."""
        for quantity in [0, -10]:
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    calculate_food_nutrition(
                        self.food,
                        quantity,
                    )

    def test_multiple_items_in_one_meal(self):
        """A meal can contain multiple food portions."""
        result = calculate_meal_nutrition([
            {"food_code": self.food_code, "quantity_g": 50},
            {"food_code": self.food_code, "quantity_g": 100},
        ])

        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(
            result["items"]["quantity_g"].sum(),
            150,
        )

    def test_unknown_food_code(self):
        """An invalid food code must raise an error."""
        with self.assertRaises(ValueError):
            calculate_meal_nutrition([
                {
                    "food_code": "INVALID_CODE",
                    "quantity_g": 100,
                }
            ])

    def test_empty_meal(self):
        """An empty meal should have zero nutrient totals."""
        result = calculate_meal_nutrition([])

        self.assertTrue(result["items"].empty)

        for value in result["totals"].values():
            self.assertEqual(value, 0.0)

    def test_daily_plan_has_four_meals(self):
        """The daily calculation should include all four meals."""
        result = calculate_daily_nutrition({
            "Breakfast": [],
            "Lunch": [],
            "Snacks": [],
            "Dinner": [],
        })

        self.assertEqual(set(result["meals"]), set(MEALS))

        for value in result["daily_totals"].values():
            self.assertEqual(value, 0.0)

    def test_daily_total_equals_meal_sum(self):
        """Full-day nutrients should equal the sum of meal totals."""
        plan = {
            "Breakfast": [
                {"food_code": self.food_code, "quantity_g": 50}
            ],
            "Lunch": [
                {"food_code": self.food_code, "quantity_g": 100}
            ],
            "Snacks": [
                {"food_code": self.food_code, "quantity_g": 25}
            ],
            "Dinner": [
                {"food_code": self.food_code, "quantity_g": 75}
            ],
        }

        result = calculate_daily_nutrition(plan)

        for nutrient, daily_value in result["daily_totals"].items():
            expected = sum(
                result["meals"][meal]["totals"][nutrient]
                for meal in MEALS
                if pd.notna(
                    result["meals"][meal]["totals"][nutrient]
                )
            )

            self.assertAlmostEqual(
                daily_value,
                expected,
                places=8,
                msg=f"Incorrect daily total for {nutrient}",
            )

    def test_missing_nutrient_remains_missing(self):
        """A missing source nutrient must not become zero."""
        food = self.food.copy()
        food["protein_g"] = float("nan")

        result = calculate_food_nutrition(food, 100)

        self.assertTrue(pd.isna(result["protein_g"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
