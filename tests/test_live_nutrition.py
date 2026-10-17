import unittest
from unittest.mock import patch

from src.live_nutrition import normalize_search_result, search_foods, get_food_details


class LiveNutritionTests(unittest.TestCase):
    def test_energy_is_converted_from_kcal_to_kj(self):
        result = normalize_search_result({
            "fdcId": 123, "description": "Test food", "dataType": "Foundation",
            "foodNutrients": [
                {"nutrientId": 1003, "nutrientName": "Protein", "value": 9, "unitName": "g"},
                {"nutrientId": 1008, "nutrientName": "Energy", "value": 100, "unitName": "kcal"},
            ],
        })
        self.assertEqual(result["food_code"], "USDA-123")
        self.assertEqual(result["protein_g"], 9)
        self.assertAlmostEqual(result["energy_kj"], 418.4)

    def test_missing_nutrients_stay_none(self):
        result = normalize_search_result({"fdcId": 1, "description": "Unknown", "foodNutrients": []})
        self.assertIsNone(result["protein_g"])
        self.assertIsNone(result["fiber_total_g"])

    def test_short_query_rejected(self):
        with self.assertRaises(ValueError):
            search_foods("x", api_key="test")

    @patch("src.live_nutrition._request_json")
    def test_search_returns_normalized_foods(self, mock_request):
        mock_request.return_value = {"foods": [{"fdcId": 7, "description": "Banana", "dataType": "Foundation", "foodNutrients": []}]}
        results = search_foods("banana", api_key="test")
        self.assertEqual(results[0]["food_name"], "Banana")
        self.assertEqual(results[0]["source_id"], 7)

    @patch("src.live_nutrition._request_json")
    def test_details_returns_record(self, mock_request):
        mock_request.return_value = {
            "fdcId": 8, "description": "Oats", "dataType": "SR Legacy",
            "foodNutrients": [{"nutrient": {"id": 1003, "name": "Protein", "unitName": "g"}, "amount": 13}],
        }
        result = get_food_details(8, api_key="test")
        self.assertEqual(result["food_name"], "Oats")
        self.assertEqual(result["protein_g"], 13)


if __name__ == "__main__":
    unittest.main()
