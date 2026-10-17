
from pathlib import Path

import pandas as pd


# ============================================================
# AAHAR AI - NUTRITION RECOMMENDATION ENGINE
# ============================================================

DATA_PATH = Path("data/processed/ifct_foods_clean.csv")

NUTRIENTS = {
    "protein": "protein_g",
    "fiber": "fiber_total_g",
    "energy": "energy_kj",
    "carbohydrates": "carbs_available_g",
    "fat": "fat_g",
}

GOAL_WEIGHTS = {
    "muscle_gain": {
        "protein": 0.60,
        "energy": 0.25,
        "carbohydrates": 0.15,
    },
    "higher_fiber": {
        "fiber": 0.70,
        "protein": 0.20,
        "carbohydrates": 0.10,
    },
    "balanced": {
        "protein": 0.30,
        "fiber": 0.30,
        "energy": 0.20,
        "carbohydrates": 0.20,
    },
}

OUTPUT_COLUMNS = [
    "food_code",
    "food_name",
    "protein_g",
    "fiber_total_g",
    "energy_kj",
    "carbs_available_g",
    "fat_g",
    "recommendation_score",
]

GAP_OUTPUT_COLUMNS = [
    "food_code",
    "food_name",
    "suggested_portion_g",
    "gap_score",
    "protein_g",
    "fiber_total_g",
    "energy_kj",
    "carbs_available_g",
    "fat_g",
]


# ============================================================
# 1. LOAD AND VALIDATE DATA
# ============================================================

def load_foods():
    """Load and validate the cleaned IFCT dataset."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}. "
            "Run src.preprocess first."
        )

    df = pd.read_csv(DATA_PATH)

    required = [
        "food_code",
        "food_name",
        *NUTRIENTS.values(),
    ]

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Dataset is missing columns: {missing}"
        )

    for column in NUTRIENTS.values():
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )

    df["food_code"] = (
        df["food_code"].astype("string").str.strip()
    )
    df["food_name"] = (
        df["food_name"].astype("string").str.strip()
    )

    df = df.dropna(subset=["food_code", "food_name"])

    df = df[
        df["food_code"].ne("")
        & df["food_name"].ne("")
    ]

    return (
        df.drop_duplicates(
            subset=["food_code"], keep="first"
        )
        .reset_index(drop=True)
    )


# ============================================================
# 2. WEIGHT HELPERS
# ============================================================

def get_normalized_weights(goal):
    """Return goal weights normalized to sum to 1."""

    if goal not in GOAL_WEIGHTS:
        raise ValueError(
            f"Unknown goal '{goal}'. "
            f"Choose from {list(GOAL_WEIGHTS)}."
        )

    weights = GOAL_WEIGHTS[goal]
    total = sum(weights.values())

    if total <= 0:
        raise ValueError(
            "Total recommendation weight must be positive."
        )

    if any(weight < 0 for weight in weights.values()):
        raise ValueError(
            "Recommendation weights cannot be negative."
        )

    return {
        nutrient: weight / total
        for nutrient, weight in weights.items()
    }


def explain_recommendation_score(goal="balanced"):
    """Explain the configured nutrient weights for a goal."""

    weights = get_normalized_weights(goal)

    reasons = {
        "protein": "Protein contribution is weighted for this goal.",
        "fiber": "Fibre contribution is weighted for this goal.",
        "energy": "Energy contribution is weighted for this goal.",
        "carbohydrates": (
            "Carbohydrate contribution is weighted for this goal."
        ),
        "fat": "Fat contribution is weighted for this goal.",
    }

    return pd.DataFrame([
        {
            "nutrient": nutrient,
            "weight": weight,
            "weight_percent": round(weight * 100, 2),
            "reason": reasons.get(nutrient, ""),
        }
        for nutrient, weight in weights.items()
    ])


# ============================================================
# 3. SCORE FOODS AND EXPLAIN CONTRIBUTIONS
# ============================================================

def _score_foods(df, goal):
    """
    Calculate relative min-max nutrient scores.

    Missing nutrients are excluded from a food's denominator.
    Contribution columns show actual score points.
    """

    df = df.copy()
    weights = get_normalized_weights(goal)

    weighted_score = pd.Series(0.0, index=df.index)
    available_weight = pd.Series(0.0, index=df.index)

    for nutrient, weight in weights.items():
        column = NUTRIENTS[nutrient]
        values = df[column]
        valid = values.dropna()

        score_column = f"{nutrient}_score_0_100"
        scaled = pd.Series(float("nan"), index=df.index)

        if not valid.empty:
            minimum = valid.min()
            maximum = valid.max()

            if maximum == minimum:
                scaled.loc[values.notna()] = 50.0
            else:
                valid_mask = values.notna()
                scaled.loc[valid_mask] = (
                    (values.loc[valid_mask] - minimum)
                    / (maximum - minimum)
                    * 100.0
                )

        df[score_column] = scaled
        present = scaled.notna()

        weighted_score.loc[present] += (
            scaled.loc[present] * weight
        )
        available_weight.loc[present] += weight

    denominator = available_weight.where(
        available_weight > 0
    )

    df["recommendation_score"] = (
        weighted_score / denominator
    )

    # Normalize weights over the nutrients available for each food.
    for nutrient, weight in weights.items():
        score_column = f"{nutrient}_score_0_100"
        contribution_column = f"{nutrient}_score_contribution"

        effective_weight = weight / denominator

        df[contribution_column] = (
            df[score_column] * effective_weight
        ).fillna(0.0)

    return df.dropna(subset=["recommendation_score"])


def recommend_foods(
    goal="balanced",
    top_n=10,
    min_protein_g=None,
    max_energy_kj=None,
):
    """Return foods ranked by weighted nutrient scores."""

    get_normalized_weights(goal)

    if (
        not isinstance(top_n, int)
        or isinstance(top_n, bool)
        or top_n < 1
    ):
        raise ValueError("top_n must be a positive integer.")

    for name, value in [
        ("min_protein_g", min_protein_g),
        ("max_energy_kj", max_energy_kj),
    ]:
        if value is not None and (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not pd.notna(value)
            or value < 0
        ):
            raise ValueError(
                f"{name} must be a non-negative number."
            )

    df = load_foods()

    if min_protein_g is not None:
        df = df[
            df["protein_g"].notna()
            & (df["protein_g"] >= min_protein_g)
        ]

    if max_energy_kj is not None:
        df = df[
            df["energy_kj"].notna()
            & (df["energy_kj"] <= max_energy_kj)
        ]

    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    df = _score_foods(df, goal)

    df = df.sort_values(
        ["recommendation_score", "food_name"],
        ascending=[False, True],
    )

    return (
        df[OUTPUT_COLUMNS]
        .head(top_n)
        .reset_index(drop=True)
    )


def explain_food_score(goal="balanced", food_code=None):
    """
    Explain each food's nutrient scores and contributions.

    Scores are calculated against the complete dataset so the
    explanation matches the ranking method.
    """

    weights = get_normalized_weights(goal)
    df = load_foods()

    scored = _score_foods(df, goal)

    if food_code is not None:
        scored = scored[
            scored["food_code"].astype(str) == str(food_code)
        ]

        if scored.empty:
            raise ValueError(
                f"Food code '{food_code}' was not found."
            )

    rows = []

    for _, food in scored.iterrows():
        for nutrient, weight in weights.items():
            column = NUTRIENTS[nutrient]
            raw_value = food[column]

            rows.append({
                "food_code": food["food_code"],
                "food_name": food["food_name"],
                "goal": goal,
                "nutrient": nutrient,
                "raw_value_per_100g": (
                    float(raw_value)
                    if pd.notna(raw_value)
                    else float("nan")
                ),
                "configured_weight_percent": round(
                    weight * 100, 2
                ),
                "scaled_nutrient_score": food[
                    f"{nutrient}_score_0_100"
                ],
                "score_point_contribution": food[
                    f"{nutrient}_score_contribution"
                ],
                "overall_score": food["recommendation_score"],
            })

    return pd.DataFrame(rows)


# ============================================================
# 4. DAILY NUTRITION-GAP RECOMMENDATIONS
# ============================================================

def suggest_foods_for_gaps(
    daily_totals,
    targets,
    portion_g=100,
    top_n=5,
    optimize_portion=False,
):
    """
    Rank foods according to remaining nutritional gaps.

    optimize_portion=False:
        Evaluate only the requested portion_g.

    optimize_portion=True:
        Evaluate 25 g, 50 g, 75 g, and 100 g portions up to
        portion_g, including portion_g if it is not one of them.

    The gap score is a prototype heuristic, not a health score.
    Nutrient amounts returned represent the suggested portion.
    """

    if (
        not isinstance(portion_g, (int, float))
        or isinstance(portion_g, bool)
        or not pd.notna(portion_g)
        or portion_g <= 0
    ):
        raise ValueError(
            "portion_g must be a positive number."
        )

    if (
        not isinstance(top_n, int)
        or isinstance(top_n, bool)
        or top_n < 1
    ):
        raise ValueError(
            "top_n must be a positive integer."
        )

    if not isinstance(optimize_portion, bool):
        raise ValueError(
            "optimize_portion must be True or False."
        )

    if not isinstance(daily_totals, dict):
        raise ValueError(
            "daily_totals must be a dictionary."
        )

    if not isinstance(targets, dict):
        raise ValueError(
            "targets must be a dictionary."
        )

    # Identify remaining gaps only where current totals and targets
    # are both known.
    gaps = {}

    for column in NUTRIENTS.values():
        target = targets.get(column)
        consumed = daily_totals.get(column)

        if target is None or consumed is None:
            continue

        try:
            target = float(target)
            consumed = float(consumed)
        except (TypeError, ValueError):
            continue

        if pd.isna(target) or pd.isna(consumed):
            continue

        if target < 0:
            raise ValueError(
                f"Target for {column} cannot be negative."
            )

        if consumed < 0:
            raise ValueError(
                f"Daily total for {column} cannot be negative."
            )

        if target > consumed:
            gaps[column] = target - consumed

    if not gaps:
        return pd.DataFrame(columns=GAP_OUTPUT_COLUMNS)

    if optimize_portion:
        portions = [
            float(size)
            for size in (25, 50, 75, 100)
            if size <= portion_g
        ]

        # Preserve custom maximum portion sizes such as 60 g.
        if float(portion_g) not in portions:
            portions.append(float(portion_g))

        portions = sorted(set(portions))
    else:
        portions = [float(portion_g)]

    foods = load_foods()
    rows = []

    for _, food in foods.iterrows():
        best_row = None
        best_score = float("-inf")

        for size in portions:
            contributions = {}
            fill_fractions = []

            # Measure the fraction of each gap this portion can fill.
            for column, remaining in gaps.items():
                value = food[column]

                if pd.isna(value):
                    continue

                amount = float(value) * size / 100.0
                contributions[column] = amount

                fill_fractions.append(
                    min(amount / remaining, 1.0)
                )

            if not fill_fractions:
                continue

            if not any(
                amount > 0
                for amount in contributions.values()
            ):
                continue

            # Penalize target overshoot for nutrients that have
            # a known value for this food and known daily total.
            overshoot_fractions = []

            for column, amount in contributions.items():
                target = targets.get(column)
                consumed = daily_totals.get(column)

                if target is None or consumed is None:
                    continue

                try:
                    target_value = float(target)
                    consumed_value = float(consumed)
                except (TypeError, ValueError):
                    continue

                if (
                    pd.isna(target_value)
                    or pd.isna(consumed_value)
                    or target_value <= 0
                ):
                    continue

                projected = consumed_value + amount
                excess = max(projected - target_value, 0.0)

                overshoot_fractions.append(
                    min(excess / target_value, 1.0)
                )

            gap_fill_score = (
                100.0
                * sum(fill_fractions)
                / len(fill_fractions)
            )

            overshoot_penalty = (
                20.0
                * sum(overshoot_fractions)
                / len(overshoot_fractions)
                if overshoot_fractions
                else 0.0
            )

            score = gap_fill_score - overshoot_penalty

            row = {
                "food_code": food["food_code"],
                "food_name": food["food_name"],
                "suggested_portion_g": size,
                "gap_score": round(score, 2),
            }

            # Return nutrient amounts for the selected portion.
            for column in NUTRIENTS.values():
                value = food[column]

                row[column] = (
                    float(value) * size / 100.0
                    if pd.notna(value)
                    else float("nan")
                )

            # Keep the best portion for each food.
            if score > best_score:
                best_score = score
                best_row = row

        if best_row is not None:
            rows.append(best_row)

    if not rows:
        return pd.DataFrame(columns=GAP_OUTPUT_COLUMNS)

    result = pd.DataFrame(rows).sort_values(
        ["gap_score", "food_name"],
        ascending=[False, True],
    )

    return (
        result[GAP_OUTPUT_COLUMNS]
        .head(top_n)
        .reset_index(drop=True)
    )


# ============================================================
# 5. PROJECTED DAILY TOTALS
# ============================================================

def add_projected_daily_totals(
    recommendations,
    daily_totals,
):
    """Calculate daily totals after adding each suggested portion."""

    if not isinstance(daily_totals, dict):
        raise ValueError(
            "daily_totals must be a dictionary."
        )

    if recommendations.empty:
        return recommendations.copy()

    result = recommendations.copy()

    for column in NUTRIENTS.values():
        projected_column = f"projected_{column}"
        current = daily_totals.get(column)

        if current is None:
            result[projected_column] = float("nan")
            continue

        try:
            current = float(current)
        except (TypeError, ValueError):
            result[projected_column] = float("nan")
            continue

        if (
            pd.isna(current)
            or column not in result.columns
        ):
            result[projected_column] = float("nan")
            continue

        result[projected_column] = result[column].apply(
            lambda amount: (
                current + float(amount)
                if pd.notna(amount)
                else float("nan")
            )
        )

    return result


# ============================================================
# 6. RUN DEMONSTRATION
# ============================================================

if __name__ == "__main__":

    print("=" * 65)
    print("AAHAR AI - RECOMMENDATION ENGINE")
    print("=" * 65)

    for goal_name in GOAL_WEIGHTS:
        print(f"\nGOAL: {goal_name}")

        recommendations = recommend_foods(
            goal=goal_name,
            top_n=5,
        )

        print("\nRanked foods:")
        print(recommendations.to_string(index=False))

        if not recommendations.empty:
            first_code = recommendations.iloc[0]["food_code"]

            print("\nScore explanation for the top food:")
            explanation = explain_food_score(
                goal=goal_name,
                food_code=first_code,
            )

            print(explanation.to_string(index=False))

        print("\nConfigured weights:")
        print(
            explain_recommendation_score(goal_name)
            .to_string(index=False)
        )

    current_totals = {
        "protein_g": 40.0,
        "fiber_total_g": 12.0,
        "energy_kj": 5000.0,
        "carbs_available_g": 100.0,
        "fat_g": 25.0,
    }

    daily_targets = {
        "protein_g": 100.0,
        "fiber_total_g": 30.0,
        "energy_kj": 9200.0,
        "carbs_available_g": 270.0,
        "fat_g": 70.0,
    }

    recommendations = suggest_foods_for_gaps(
        daily_totals=current_totals,
        targets=daily_targets,
        portion_g=100,
        top_n=5,
        optimize_portion=True,
    )

    projected = add_projected_daily_totals(
        recommendations,
        current_totals,
    )

    print("\nDaily nutrition-gap recommendations:")
    print(projected.to_string(index=False))
