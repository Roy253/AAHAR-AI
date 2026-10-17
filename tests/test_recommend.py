
import unittest
import pandas as pd

from src.recommend import (
    recommend_foods,
    suggest_foods_for_gaps,
    add_projected_daily_totals,
    OUTPUT_COLUMNS,
    GAP_OUTPUT_COLUMNS,
)


class TestRecommendationEngine(unittest.TestCase):

    def setUp(self):
        self.daily_totals = {
            "protein_g": 40.0,
            "fiber_total_g": 12.0,
            "energy_kj": 5000.0,
            "carbs_available_g": 100.0,
            "fat_g": 25.0,
        }

        self.targets = {
            "protein_g": 100.0,
            "fiber_total_g": 30.0,
            "energy_kj": 9200.0,
            "carbs_available_g": 270.0,
            "fat_g": 70.0,
        }

    def test_all_goals_return_valid_columns(self):
        for goal in ["muscle_gain", "higher_fiber", "balanced"]:
            result = recommend_foods(goal=goal, top_n=5)

            self.assertTrue(
                set(OUTPUT_COLUMNS).issubset(result.columns)
            )
            self.assertLessEqual(len(result), 5)

    def test_recommendation_scores_are_bounded(self):
        result = recommend_foods(top_n=10)

        if not result.empty:
            self.assertTrue(
                result["recommendation_score"].between(0, 100).all()
            )

    def test_invalid_goal_is_rejected(self):
        with self.assertRaises(ValueError):
            recommend_foods(goal="unknown_goal")

    def test_invalid_top_n_is_rejected(self):
        with self.assertRaises(ValueError):
            recommend_foods(top_n=0)

    def test_filters_return_only_matching_foods(self):
        baseline = recommend_foods(top_n=100)

        if baseline.empty or baseline["protein_g"].dropna().empty:
            self.skipTest("Dataset has no usable protein values.")

        minimum = float(baseline["protein_g"].dropna().median())

        result = recommend_foods(
            top_n=100,
            min_protein_g=minimum,
        )

        if not result.empty:
            self.assertTrue(
                (result["protein_g"] >= minimum).all()
            )

    def test_invalid_portion_is_rejected(self):
        with self.assertRaises(ValueError):
            suggest_foods_for_gaps(
                self.daily_totals,
                self.targets,
                portion_g=0,
            )

    def test_all_targets_met_returns_no_suggestions(self):
        result = suggest_foods_for_gaps(
            daily_totals=self.targets,
            targets=self.targets,
        )

        self.assertTrue(result.empty)
        self.assertTrue(
            set(GAP_OUTPUT_COLUMNS).issubset(result.columns)
        )

    def test_gap_recommendations_have_valid_scores(self):
        result = suggest_foods_for_gaps(
            daily_totals=self.daily_totals,
            targets=self.targets,
            portion_g=50,
            top_n=5,
        )

        self.assertLessEqual(len(result), 5)

        if not result.empty:
            self.assertTrue(
                result["gap_score"].between(0, 100).all()
            )
            self.assertTrue(
                (result["suggested_portion_g"] == 50).all()
            )

    def test_missing_current_nutrient_is_skipped(self):
        totals = self.daily_totals.copy()
        totals["protein_g"] = None

        result = suggest_foods_for_gaps(
            daily_totals=totals,
            targets=self.targets,
            top_n=5,
        )

        self.assertLessEqual(len(result), 5)

    def test_projected_protein_is_calculated_correctly(self):
        recommendations = suggest_foods_for_gaps(
            daily_totals=self.daily_totals,
            targets=self.targets,
            portion_g=50,
            top_n=3,
        )

        projected = add_projected_daily_totals(
            recommendations,
            self.daily_totals,
        )

        if projected.empty:
            self.skipTest("No suitable recommendations available.")

        for _, row in projected.iterrows():
            if pd.notna(row["protein_g"]):
                self.assertAlmostEqual(
                    row["projected_protein_g"],
                    self.daily_totals["protein_g"] + row["protein_g"],
                    places=6,
                )

    def test_missing_current_total_stays_missing(self):
        recommendations = suggest_foods_for_gaps(
            daily_totals=self.daily_totals,
            targets=self.targets,
            top_n=3,
        )

        totals = self.daily_totals.copy()
        totals["protein_g"] = None

        projected = add_projected_daily_totals(
            recommendations,
            totals,
        )

        if not projected.empty:
            self.assertTrue(
                projected["projected_protein_g"].isna().all()
            )


if __name__ == "__main__":
    unittest.main()
