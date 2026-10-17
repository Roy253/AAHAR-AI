
from src.recommend import recommend_foods, GOAL_WEIGHTS


def main():
    print("AAHAR AI — RECOMMENDATION EVALUATION")
    print("=" * 45)

    # Test every supported goal.
    for goal in GOAL_WEIGHTS:
        result = recommend_foods(goal=goal, top_n=10)

        assert len(result) <= 10, f"{goal}: returned too many rows"
        assert "recommendation_score" in result.columns
        assert result["food_code"].is_unique
        assert result["recommendation_score"].notna().all()

        scores = result["recommendation_score"].tolist()
        assert scores == sorted(scores, reverse=True), (
            f"{goal}: results are not sorted by score"
        )

        print(f"PASS: {goal} returned {len(result)} ranked foods")

    # Test protein filter.
    protein_result = recommend_foods(
        goal="muscle_gain",
        top_n=10,
        min_protein_g=15,
    )
    assert (protein_result["protein_g"] >= 15).all()
    print("PASS: minimum-protein filter")

    # Test energy filter.
    energy_result = recommend_foods(
        goal="balanced",
        top_n=10,
        max_energy_kj=2000,
    )
    assert (energy_result["energy_kj"] <= 2000).all()
    print("PASS: maximum-energy filter")

    # Test invalid goal.
    try:
        recommend_foods(goal="unknown_goal")
    except ValueError:
        print("PASS: invalid goal rejected")
    else:
        raise AssertionError("Invalid goal was not rejected")

    print("\nAll evaluation checks passed.")


if __name__ == "__main__":
    main()
