
from pathlib import Path

import pandas as pd
import streamlit as st

from src.recommend import (
    NUTRIENTS,
    add_projected_daily_totals,
    suggest_foods_for_gaps,
)


# ============================================================
# AAHAR AI - NUTRITION PLANNER
# ============================================================

st.set_page_config(
    page_title="AAHAR AI | Nutrition Planner",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT_DIR = Path(__file__).resolve().parent
DATA_PATH = ROOT_DIR / "data" / "processed" / "ifct_foods_clean.csv"

NUTRIENT_COLUMNS = [
    "protein_g",
    "fiber_total_g",
    "energy_kj",
    "carbs_available_g",
    "fat_g",
]

NUTRIENT_LABELS = {
    "protein_g": "Protein (g)",
    "fiber_total_g": "Fibre (g)",
    "energy_kj": "Energy (kJ)",
    "carbs_available_g": "Carbohydrates (g)",
    "fat_g": "Fat (g)",
}

MEALS = [
    "Breakfast",
    "Lunch",
    "Dinner",
    "Snacks",
]

SYSTEM_TOP_N = 5
DEFAULT_PORTION_G = 100


# ============================================================
# 1. DIETARY GOAL PROFILES
# ============================================================

GOAL_PROFILES = {
    "Balanced Nutrition": {
        "protein_g": 60.0,
        "fiber_total_g": 30.0,
        "energy_kj": 8400.0,
        "carbs_available_g": 270.0,
        "fat_g": 70.0,
        "recommendation_goal": "balanced",
    },
    "Muscle Gain": {
        "protein_g": 100.0,
        "fiber_total_g": 30.0,
        "energy_kj": 10500.0,
        "carbs_available_g": 300.0,
        "fat_g": 75.0,
        "recommendation_goal": "muscle_gain",
    },
    "Weight Management": {
        "protein_g": 70.0,
        "fiber_total_g": 30.0,
        "energy_kj": 7500.0,
        "carbs_available_g": 220.0,
        "fat_g": 60.0,
        "recommendation_goal": "balanced",
    },
    "High Protein": {
        "protein_g": 100.0,
        "fiber_total_g": 30.0,
        "energy_kj": 8400.0,
        "carbs_available_g": 250.0,
        "fat_g": 70.0,
        "recommendation_goal": "muscle_gain",
    },
    "High Fibre": {
        "protein_g": 60.0,
        "fiber_total_g": 35.0,
        "energy_kj": 8400.0,
        "carbs_available_g": 270.0,
        "fat_g": 70.0,
        "recommendation_goal": "higher_fiber",
    },
}


# ============================================================
# 2. LOAD AND VALIDATE FOOD DATA
# ============================================================

@st.cache_data
def load_food_data():
    """Load the processed IFCT food dataset."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {DATA_PATH}"
        )

    foods = pd.read_csv(DATA_PATH)

    required_columns = [
        "food_code",
        "food_name",
        *NUTRIENT_COLUMNS,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in foods.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Dataset is missing columns: {missing_columns}"
        )

    foods["food_code"] = (
        foods["food_code"].astype("string").str.strip()
    )

    foods["food_name"] = (
        foods["food_name"].astype("string").str.strip()
    )

    for column in NUTRIENT_COLUMNS:
        foods[column] = pd.to_numeric(
            foods[column], errors="coerce"
        )

    foods = foods.dropna(
        subset=["food_code", "food_name"]
    )

    foods = foods[
        foods["food_code"].ne("")
        & foods["food_name"].ne("")
    ]

    foods = foods.drop_duplicates(
        subset=["food_code"], keep="first"
    )

    return foods.reset_index(drop=True)


try:
    foods = load_food_data()
except Exception as exc:
    st.error(f"Unable to load food data: {exc}")
    st.stop()


# ============================================================
# 3. SESSION STATE
# ============================================================

if "meal_plan" not in st.session_state:
    st.session_state.meal_plan = {
        meal: [] for meal in MEALS
    }

if "selected_goal" not in st.session_state:
    st.session_state.selected_goal = "Balanced Nutrition"

if "custom_targets" not in st.session_state:
    st.session_state.custom_targets = None

if "portion_counter" not in st.session_state:
    st.session_state.portion_counter = 0


# ============================================================
# 4. NUTRITION CALCULATIONS
# ============================================================

def calculate_food_nutrients(food, portion_g):
    """
    Calculate nutrient amounts for a food portion.

    Dataset values are assumed to be per 100 g.
    Missing values remain missing, not zero.
    """

    result = {}

    for column in NUTRIENT_COLUMNS:
        value = food[column]

        if pd.isna(value):
            result[column] = float("nan")
        else:
            result[column] = (
                float(value) * float(portion_g) / 100.0
            )

    return result


def calculate_meal_nutrition(meal_items):
    """Calculate nutrient totals for one meal."""

    totals = {
        column: 0.0
        for column in NUTRIENT_COLUMNS
    }

    unknown_nutrients = set()

    for item in meal_items:
        food = foods.loc[
            foods["food_code"].astype(str)
            == str(item["food_code"])
        ]

        if food.empty:
            continue

        food = food.iloc[0]

        nutrients = calculate_food_nutrients(
            food, item["portion_g"]
        )

        for column, value in nutrients.items():
            if pd.isna(value):
                unknown_nutrients.add(column)
            else:
                totals[column] += value

    # Do not report incomplete totals as fully accurate.
    for column in unknown_nutrients:
        totals[column] = float("nan")

    return totals


def calculate_daily_nutrition():
    """Calculate daily totals from all meals."""

    totals = {
        column: 0.0
        for column in NUTRIENT_COLUMNS
    }

    unknown_nutrients = set()

    for meal in MEALS:
        meal_totals = calculate_meal_nutrition(
            st.session_state.meal_plan[meal]
        )

        for column, value in meal_totals.items():
            if pd.isna(value):
                unknown_nutrients.add(column)
            else:
                totals[column] += value

    for column in unknown_nutrients:
        totals[column] = float("nan")

    return totals


def get_current_targets():
    """Return the active nutrient targets."""

    if st.session_state.custom_targets is not None:
        return st.session_state.custom_targets.copy()

    profile = GOAL_PROFILES[
        st.session_state.selected_goal
    ]

    return {
        column: profile[column]
        for column in NUTRIENT_COLUMNS
    }


def format_nutrient(value, column):
    """Format a nutrient amount for display."""

    if pd.isna(value):
        return "Unknown"

    decimals = 0 if column == "energy_kj" else 1

    return f"{value:.{decimals}f}"


# ============================================================
# 5. EXPORT HELPERS
# ============================================================

def build_meal_plan_export():
    """Build a CSV-ready table of all selected foods."""

    rows = []

    for meal in MEALS:
        for item in st.session_state.meal_plan[meal]:
            matching = foods.loc[
                foods["food_code"].astype(str)
                == str(item["food_code"])
            ]

            if matching.empty:
                continue

            food = matching.iloc[0]

            nutrients = calculate_food_nutrients(
                food, item["portion_g"]
            )

            row = {
                "meal": meal,
                "food_code": item["food_code"],
                "food_name": item["food_name"],
                "portion_g": item["portion_g"],
            }

            row.update(nutrients)
            rows.append(row)

    columns = [
        "meal",
        "food_code",
        "food_name",
        "portion_g",
        *NUTRIENT_COLUMNS,
    ]

    return pd.DataFrame(rows, columns=columns)


def build_daily_summary_export():
    """Build a CSV-ready daily nutrition summary."""

    totals = calculate_daily_nutrition()
    targets = get_current_targets()

    rows = []

    for column in NUTRIENT_COLUMNS:
        consumed = totals[column]
        target = targets[column]

        if pd.isna(consumed):
            remaining = float("nan")
        else:
            remaining = max(target - consumed, 0.0)

        rows.append({
            "nutrient": NUTRIENT_LABELS[column],
            "consumed": consumed,
            "target": target,
            "remaining_to_target": remaining,
            "unit": "kJ" if column == "energy_kj" else "g",
        })

    return pd.DataFrame(rows)


# ============================================================
# 6. SIDEBAR - GOALS AND TARGETS
# ============================================================

st.sidebar.title("🥗 AAHAR AI")
st.sidebar.caption("Personal Nutrition Planner")
st.sidebar.divider()

goal_names = list(GOAL_PROFILES.keys())

selected_goal = st.sidebar.selectbox(
    "Choose your dietary goal",
    goal_names,
    key="goal_selector",
    index=goal_names.index(
        st.session_state.selected_goal
    ),
)

if selected_goal != st.session_state.selected_goal:
    st.session_state.selected_goal = selected_goal
    st.session_state.custom_targets = None

st.sidebar.caption(
    "Profile targets are illustrative defaults, not "
    "personalized medical or dietary prescriptions."
)

st.sidebar.divider()

with st.sidebar.expander(
    "Customize daily targets",
    expanded=False,
):
    current_profile = GOAL_PROFILES[
        st.session_state.selected_goal
    ]

    current_targets = get_current_targets()

    energy_kcal_default = (
        current_targets["energy_kj"] / 4.184
    )

    protein_target = st.number_input(
        "Protein target (g)",
        min_value=0.0,
        max_value=500.0,
        value=float(current_targets["protein_g"]),
        step=5.0,
        key="target_protein",
    )

    fiber_target = st.number_input(
        "Fibre target (g)",
        min_value=0.0,
        max_value=150.0,
        value=float(current_targets["fiber_total_g"]),
        step=5.0,
        key="target_fiber",
    )

    energy_target_kcal = st.number_input(
        "Energy target (kcal)",
        min_value=0.0,
        max_value=10000.0,
        value=float(energy_kcal_default),
        step=50.0,
        key="target_energy",
    )

    carbs_target = st.number_input(
        "Carbohydrate target (g)",
        min_value=0.0,
        max_value=1000.0,
        value=float(current_targets["carbs_available_g"]),
        step=10.0,
        key="target_carbs",
    )

    fat_target = st.number_input(
        "Fat target (g)",
        min_value=0.0,
        max_value=500.0,
        value=float(current_targets["fat_g"]),
        step=5.0,
        key="target_fat",
    )

    if st.button(
        "Apply custom targets",
        key="apply_custom_targets",
        use_container_width=True,
    ):
        st.session_state.custom_targets = {
            "protein_g": protein_target,
            "fiber_total_g": fiber_target,
            "energy_kj": energy_target_kcal * 4.184,
            "carbs_available_g": carbs_target,
            "fat_g": fat_target,
        }
        st.rerun()

    if st.button(
        "Reset to profile defaults",
        key="reset_targets",
        use_container_width=True,
    ):
        st.session_state.custom_targets = None
        st.rerun()


# ============================================================
# 7. MAIN HEADER
# ============================================================

st.title("🥗 AAHAR AI")
st.subheader("Your Food. Your Goals. Your Nutrition.")

st.write(
    "Build a daily meal plan using food composition data "
    "from the processed Indian Food Composition Tables dataset. "
    "Track nutrients and explore recommendations based on "
    "your selected dietary goal."
)

st.caption(
    f"Food database: {len(foods)} foods | "
    "Nutrient values are calculated from per-100 g data."
)

st.divider()


# ============================================================
# 8. ADD FOOD TO A MEAL
# ============================================================

st.header("1. Build Your Meal Plan")

add_column, detail_column = st.columns(
    [1.1, 0.9],
    gap="large",
)

with add_column:
    st.subheader("Add a food")

    selected_meal = st.selectbox(
        "Select meal",
        MEALS,
        key="add_food_meal",
    )

    food_options = foods[
        ["food_code", "food_name"]
    ].copy()

    food_options["display"] = (
        food_options["food_name"].astype(str)
        + " ("
        + food_options["food_code"].astype(str)
        + ")"
    )

    food_options = food_options.sort_values(
        "food_name"
    )

    selected_display = st.selectbox(
        "Search and select food",
        food_options["display"].tolist(),
        key="food_selector",
    )

    selected_row = food_options.loc[
        food_options["display"] == selected_display
    ].iloc[0]

    selected_food = foods.loc[
        foods["food_code"].astype(str)
        == str(selected_row["food_code"])
    ].iloc[0]

    portion_g = st.number_input(
        "Portion size (grams)",
        min_value=1.0,
        max_value=2000.0,
        value=100.0,
        step=25.0,
        key="add_food_portion",
    )

    if st.button(
        "➕ Add food to meal",
        key="add_food_button",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.portion_counter += 1

        st.session_state.meal_plan[
            selected_meal
        ].append({
            "item_id": st.session_state.portion_counter,
            "food_code": str(selected_food["food_code"]),
            "food_name": str(selected_food["food_name"]),
            "portion_g": float(portion_g),
        })

        st.rerun()

with detail_column:
    st.subheader("Selected food details")

    st.write(f"**Food:** {selected_food['food_name']}")
    st.write(f"**IFCT code:** {selected_food['food_code']}")
    st.write(f"**Reference basis:** 100 g")
    st.write(f"**Selected portion:** {portion_g:.0f} g")

    nutrient_preview = calculate_food_nutrients(
        selected_food, portion_g
    )

    detail_rows = []

    for column in NUTRIENT_COLUMNS:
        detail_rows.append({
            "Nutrient": NUTRIENT_LABELS[column],
            "Amount": format_nutrient(
                nutrient_preview[column], column
            ),
        })

    st.dataframe(
        pd.DataFrame(detail_rows),
        hide_index=True,
        use_container_width=True,
    )


# ============================================================
# 9. DISPLAY MEALS AND REMOVE FOODS
# ============================================================

st.divider()
st.header("2. Your Meals")

for meal in MEALS:
    meal_items = st.session_state.meal_plan[meal]
    meal_totals = calculate_meal_nutrition(meal_items)

    with st.expander(
        f"{meal} — {len(meal_items)} food item(s)",
        expanded=(meal == "Breakfast"),
    ):
        if not meal_items:
            st.info(
                f"No foods added to {meal.lower()} yet."
            )
            continue

        for item in meal_items:
            item_col, portion_col, remove_col = st.columns(
                [3, 1, 1],
                vertical_alignment="center",
            )

            with item_col:
                st.write(f"**{item['food_name']}**")
                st.caption(
                    f"Code: {item['food_code']}"
                )

            with portion_col:
                st.write(
                    f"{item['portion_g']:.0f} g"
                )

            with remove_col:
                if st.button(
                    "Remove",
                    key=f"remove_{meal}_{item['item_id']}",
                ):
                    st.session_state.meal_plan[meal] = [
                        existing
                        for existing in st.session_state.meal_plan[meal]
                        if existing["item_id"] != item["item_id"]
                    ]
                    st.rerun()

        meal_summary = pd.DataFrame([
            {
                "Nutrient": NUTRIENT_LABELS[column],
                "Amount": format_nutrient(
                    meal_totals[column], column
                ),
            }
            for column in NUTRIENT_COLUMNS
        ])

        st.markdown("**Meal nutrition summary**")

        st.dataframe(
            meal_summary,
            hide_index=True,
            use_container_width=True,
        )


# ============================================================
# 10. DAILY NUTRITION DASHBOARD
# ============================================================

st.divider()
st.header("3. Daily Nutrition Dashboard")

daily_totals = calculate_daily_nutrition()
targets = get_current_targets()

metric_columns = st.columns(5)

for index, column in enumerate(NUTRIENT_COLUMNS):
    with metric_columns[index]:
        st.metric(
            label=NUTRIENT_LABELS[column],
            value=format_nutrient(
                daily_totals[column], column
            ),
            delta=(
                None
                if pd.isna(daily_totals[column])
                else (
                    f"{daily_totals[column] - targets[column]:+.1f}"
                )
            ),
            help=(
                "Delta is consumed amount minus target. "
                "Positive values indicate the target has been exceeded."
            ),
        )

st.subheader("Progress against daily targets")

progress_rows = []

for column in NUTRIENT_COLUMNS:
    consumed = daily_totals[column]
    target = targets[column]

    if pd.isna(consumed):
        percentage = float("nan")
        remaining = float("nan")
        status = "Unknown — missing nutrient data"
    else:
        percentage = (
            consumed / target * 100
            if target > 0
            else float("nan")
        )

        remaining = max(target - consumed, 0.0)

        if target > 0 and consumed >= target:
            status = "Target reached or exceeded"
        elif target > 0:
            status = "Below target"
        else:
            status = "No target set"

    progress_rows.append({
        "Nutrient": NUTRIENT_LABELS[column],
        "Consumed": consumed,
        "Target": target,
        "Remaining": remaining,
        "Progress (%)": percentage,
        "Status": status,
    })

    st.write(f"**{NUTRIENT_LABELS[column]}**")

    if pd.isna(percentage):
        st.caption(
            "Progress unavailable because the total is unknown "
            "or the target is zero."
        )
    else:
        st.progress(
            min(max(percentage / 100.0, 0.0), 1.0)
        )
        st.caption(
            f"{percentage:.1f}% of target | "
            f"{status}"
        )

progress_df = pd.DataFrame(progress_rows)

with st.expander("View nutrition progress table"):
    st.dataframe(
        progress_df,
        hide_index=True,
        use_container_width=True,
    )


# ============================================================
# 11. AI-STYLE NUTRITION RECOMMENDATIONS
# ============================================================

st.divider()
st.header("4. Food Recommendations")

st.write(
    "Recommendations are ranked using the remaining nutrient "
    "gaps and candidate portion sizes. The scores are heuristic "
    "ranking scores, not clinical assessments."
)

recommendation_goal = GOAL_PROFILES[
    st.session_state.selected_goal
]["recommendation_goal"]

recommendation_column, portion_column = st.columns(2)

with recommendation_column:
    st.write(
        f"**Selected profile:** "
        f"{st.session_state.selected_goal}"
    )

with portion_column:
    max_recommendation_portion = st.selectbox(
        "Maximum candidate portion",
        [50, 75, 100],
        index=2,
        key="recommendation_max_portion",
        format_func=lambda value: f"{value} g",
    )

recommendation_targets = {
    column: targets[column]
    for column in NUTRIENT_COLUMNS
}

recommendations = pd.DataFrame()

try:
    recommendations = suggest_foods_for_gaps(
        daily_totals=daily_totals,
        targets=recommendation_targets,
        portion_g=float(max_recommendation_portion),
        top_n=SYSTEM_TOP_N,
        optimize_portion=True,
    )

except Exception as exc:
    st.error(
        "The recommendation engine could not generate "
        "recommendations."
    )
    st.exception(exc)

if recommendations.empty:
    st.info(
        "No recommendations are available. Add foods to your "
        "meal plan, check your targets, or verify that the "
        "dataset contains nutrient values for the remaining gaps."
    )

else:
    display_columns = [
        "food_name",
        "suggested_portion_g",
        "gap_score",
        *NUTRIENT_COLUMNS,
    ]

    display_recommendations = recommendations[
        display_columns
    ].copy()

    display_recommendations = display_recommendations.rename(
        columns={
            "food_name": "Food",
            "suggested_portion_g": "Suggested portion (g)",
            "gap_score": "Gap score",
            "protein_g": "Protein (g)",
            "fiber_total_g": "Fibre (g)",
            "energy_kj": "Energy (kJ)",
            "carbs_available_g": "Carbohydrates (g)",
            "fat_g": "Fat (g)",
        }
    )

    st.dataframe(
        display_recommendations,
        hide_index=True,
        use_container_width=True,
    )

    st.caption(
        "The gap score rewards filling remaining nutrient gaps "
        "and penalizes some target overshoots. It is not a "
        "validated measure of food healthfulness."
    )

    st.subheader("Recommendation explanation")

    recommendation_options = recommendations[
        ["food_code", "food_name", "suggested_portion_g"]
    ].copy()

    recommendation_options["display"] = (
        recommendation_options["food_name"].astype(str)
        + " — "
        + recommendation_options["suggested_portion_g"]
        .map(lambda value: f"{value:.0f} g")
        + " ("
        + recommendation_options["food_code"].astype(str)
        + ")"
    )

    selected_recommendation_display = st.selectbox(
        "Choose a recommendation to inspect",
        recommendation_options["display"].tolist(),
        key="recommendation_preview",
    )

    selected_recommendation = recommendation_options.loc[
        recommendation_options["display"]
        == selected_recommendation_display
    ].iloc[0]

    selected_recommendation_row = recommendations.loc[
        recommendations["food_code"].astype(str)
        == str(selected_recommendation["food_code"])
    ]

    selected_recommendation_row = (
        selected_recommendation_row.loc[
            selected_recommendation_row["suggested_portion_g"]
            == selected_recommendation["suggested_portion_g"]
        ].iloc[0]
    )

    preview_col, add_col = st.columns(
        [2, 1],
        vertical_alignment="center",
    )

    with preview_col:
        st.write(
            f"**{selected_recommendation_row['food_name']}**"
        )

        st.write(
            f"Suggested portion: "
            f"{selected_recommendation_row['suggested_portion_g']:.0f} g"
        )

        st.write(
            f"Gap score: "
            f"{selected_recommendation_row['gap_score']:.2f}"
        )

        preview_nutrients = pd.DataFrame([
            {
                "Nutrient": NUTRIENT_LABELS[column],
                "Amount in suggested portion": format_nutrient(
                    selected_recommendation_row[column], column
                ),
            }
            for column in NUTRIENT_COLUMNS
        ])

        st.dataframe(
            preview_nutrients,
            hide_index=True,
            use_container_width=True,
        )

    with add_col:
        st.write("**Add recommendation**")

        destination_meal = st.selectbox(
            "Add to meal",
            MEALS,
            index=3,
            key="recommendation_destination_meal",
        )

        if st.button(
            "Add recommended food",
            key="add_recommended_food",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.portion_counter += 1

            st.session_state.meal_plan[
                destination_meal
            ].append({
                "item_id": st.session_state.portion_counter,
                "food_code": str(
                    selected_recommendation_row["food_code"]
                ),
                "food_name": str(
                    selected_recommendation_row["food_name"]
                ),
                "portion_g": float(
                    selected_recommendation_row[
                        "suggested_portion_g"
                    ]
                ),
            })

            st.rerun()

    # Show projected totals after adding each candidate.
    st.subheader("Projected daily nutrition")

    projected = add_projected_daily_totals(
        recommendations,
        daily_totals,
    )

    if not projected.empty:
        projected_rows = []

        for _, candidate in projected.iterrows():
            row = {
                "Food": candidate["food_name"],
                "Portion (g)": candidate["suggested_portion_g"],
            }

            for column in NUTRIENT_COLUMNS:
                row[
                    f"Projected {NUTRIENT_LABELS[column]}"
                ] = candidate.get(
                    f"projected_{column}", float("nan")
                )

            projected_rows.append(row)

        st.dataframe(
            pd.DataFrame(projected_rows),
            hide_index=True,
            use_container_width=True,
        )


# ============================================================
# 12. CSV EXPORTS
# ============================================================

st.divider()
st.header("5. Export Your Nutrition Report")

meal_export = build_meal_plan_export()
summary_export = build_daily_summary_export()

export_column_1, export_column_2 = st.columns(2)

with export_column_1:
    st.subheader("Meal plan CSV")

    st.write(
        "Export each selected food, its meal, portion size, "
        "and calculated nutrient amounts."
    )

    st.download_button(
        label="Download meal plan CSV",
        data=meal_export.to_csv(index=False).encode("utf-8"),
        file_name="aahar_meal_plan.csv",
        mime="text/csv",
        key="download_meal_plan",
        use_container_width=True,
    )

with export_column_2:
    st.subheader("Daily nutrition summary CSV")

    st.write(
        "Export consumed amounts, targets, and remaining "
        "amounts for each nutrient."
    )

    st.download_button(
        label="Download daily summary CSV",
        data=summary_export.to_csv(index=False).encode("utf-8"),
        file_name="aahar_daily_nutrition.csv",
        mime="text/csv",
        key="download_daily_summary",
        use_container_width=True,
    )


# ============================================================
# 13. RESET MEAL PLAN
# ============================================================

st.divider()

with st.expander("Reset meal plan"):
    st.warning(
        "This clears all foods currently added to your meals."
    )

    if st.button(
        "Clear all meals",
        key="clear_all_meals",
    ):
        st.session_state.meal_plan = {
            meal: [] for meal in MEALS
        }

        st.rerun()


# ============================================================
# 14. FOOTER
# ============================================================

st.divider()

st.caption(
    "AAHAR AI | Nutrition recommendation prototype | "
    "Food nutrient values are based on the processed IFCT dataset."
)

st.caption(
    "This application is for educational and informational use. "
    "Its recommendation scores and default targets are not "
    "medical advice or individualized dietary prescriptions."
)
