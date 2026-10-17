
import pandas as pd

from src.ollama_client import ask_ollama
from src.recommend import (
    suggest_foods_for_gaps,
    add_projected_daily_totals,
)

# Example daily nutrition data for testing.
# These are test values, not your actual daily intake.
daily_totals = {
    "protein_g": 40.0,
    "fiber_total_g": 12.0,
    "energy_kj": 5000.0,
    "carbs_available_g": 100.0,
    "fat_g": 25.0,
}

targets = {
    "protein_g": 100.0,
    "fiber_total_g": 30.0,
    "energy_kj": 9200.0,
    "carbs_available_g": 270.0,
    "fat_g": 70.0,
}

print("AAHAR AI INTEGRATION TEST")
print("=" * 40)

try:
    # Step 1: Run the existing recommendation engine.
    recommendations = suggest_foods_for_gaps(
        daily_totals=daily_totals,
        targets=targets,
        portion_g=100,
        top_n=5,
        optimize_portion=True,
    )

    if recommendations.empty:
        print(
            "No recommendations returned. "
            "Check your IFCT dataset and nutrition gaps."
        )
        raise SystemExit(0)

    projected = add_projected_daily_totals(
        recommendations,
        daily_totals,
    )

    print("\nActual recommendations from your dataset:")
    print(
        projected[
            [
                "food_name",
                "suggested_portion_g",
                "gap_score",
            ]
        ].to_string(index=False)
    )

    # Step 2: Send the actual results to local Ollama.
    safe_data = projected[
        [
            "food_name",
            "suggested_portion_g",
            "gap_score",
            "protein_g",
            "fiber_total_g",
            "energy_kj",
            "carbs_available_g",
            "fat_g",
        ]
    ].to_dict(orient="records")

    prompt = f"""
You are AAHAR AI, a nutrition explanation assistant.

The following are actual recommendations returned by the
existing AAHAR recommendation engine.

Current daily nutrition totals:
{daily_totals}

Daily targets:
{targets}

Recommended foods and their nutrient amounts for the
suggested portions:
{safe_data}

Explain in simple language:
1. Which foods the engine recommended.
2. Why adding a variety of foods can help.
3. How the student might include these foods in meals.

Rules:
- Do not change the recommendation ranking.
- Do not invent nutrient values or prices.
- Nutrient amounts in the records refer to the suggested portions.
- Do not claim a food fixes a medical condition.
- If a value is missing, say it is unavailable.
"""

    print("\nGenerating explanation with local Ollama...")
    answer = ask_ollama(prompt)

    print("\nAAHAR AI EXPLANATION")
    print("=" * 40)
    print(answer)

except FileNotFoundError as error:
    print(f"\nDataset error: {error}")

except (ValueError, RuntimeError) as error:
    print(f"\nIntegration test failed: {error}")

except Exception as error:
    print(f"\nUnexpected error: {error}")
