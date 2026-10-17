from pathlib import Path
import os

import pandas as pd
import streamlit as st

from src.live_nutrition import NutritionAPIError, search_foods

st.set_page_config(page_title="AAHAR AI | Global Nutrition Planner", page_icon="🥗", layout="wide")

# Lightweight custom styling: polished cards, clear hierarchy, and comfortable spacing.
st.markdown("""
<style>
    .block-container {max-width: 1220px; padding-top: 1.5rem; padding-bottom: 3rem;}
    [data-testid="stAppViewContainer"] {background: linear-gradient(180deg, rgba(21, 128, 61, .055), transparent 280px);}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.18);}
    .aahar-hero {padding: 1.45rem 1.6rem; border-radius: 22px; margin-bottom: 1.2rem;
        background: linear-gradient(120deg, #14532d, #15803d 62%, #65a30d); color: white;}
    .aahar-hero h1 {color: white; font-size: 2.15rem; margin: 0 0 .35rem 0;}
    .aahar-hero p {color: #ecfdf5; margin: 0; font-size: 1rem;}
    div[data-testid="stMetric"] {background: rgba(128,128,128,.07); border: 1px solid rgba(128,128,128,.15); padding: 14px 16px; border-radius: 15px;}
    div[data-testid="stForm"], div[data-testid="stExpander"] {border-radius: 14px;}
    div.stButton > button, div.stDownloadButton > button {border-radius: 10px; font-weight: 600;}
    .aahar-note {font-size: .88rem; opacity: .82;}
</style>
""", unsafe_allow_html=True)

NUTRIENTS = ["protein_g", "fiber_total_g", "energy_kj", "carbs_available_g", "fat_g"]
LABELS = {
    "protein_g": "Protein (g)",
    "fiber_total_g": "Fibre (g)",
    "energy_kj": "Energy (kJ)",
    "carbs_available_g": "Carbohydrates (g)",
    "fat_g": "Fat (g)",
}
MEALS = ["Breakfast", "Lunch", "Dinner", "Snacks"]
GOALS = {
    "Balanced Nutrition": dict(protein_g=60, fiber_total_g=30, energy_kj=8400, carbs_available_g=270, fat_g=70),
    "Muscle Gain": dict(protein_g=100, fiber_total_g=30, energy_kj=10500, carbs_available_g=300, fat_g=75),
    "Weight Management": dict(protein_g=70, fiber_total_g=30, energy_kj=7500, carbs_available_g=220, fat_g=60),
    "High Protein": dict(protein_g=100, fiber_total_g=30, energy_kj=8400, carbs_available_g=250, fat_g=70),
    "High Fibre": dict(protein_g=60, fiber_total_g=35, energy_kj=8400, carbs_available_g=270, fat_g=70),
}
GOAL_WEIGHTS = {
    "Balanced Nutrition": {"protein_g": .25, "fiber_total_g": .25, "energy_kj": .15, "carbs_available_g": .20, "fat_g": .15},
    "Muscle Gain": {"protein_g": .50, "fiber_total_g": .10, "energy_kj": .20, "carbs_available_g": .15, "fat_g": .05},
    "Weight Management": {"protein_g": .25, "fiber_total_g": .30, "energy_kj": .10, "carbs_available_g": .20, "fat_g": .15},
    "High Protein": {"protein_g": .60, "fiber_total_g": .10, "energy_kj": .10, "carbs_available_g": .15, "fat_g": .05},
    "High Fibre": {"protein_g": .15, "fiber_total_g": .60, "energy_kj": .10, "carbs_available_g": .10, "fat_g": .05},
}

if "meal_plan" not in st.session_state:
    st.session_state.meal_plan = {meal: [] for meal in MEALS}
if "goal" not in st.session_state:
    st.session_state.goal = "Balanced Nutrition"
if "custom_targets" not in st.session_state:
    st.session_state.custom_targets = None
if "item_id" not in st.session_state:
    st.session_state.item_id = 0
if "live_results" not in st.session_state:
    st.session_state.live_results = []
if "last_query" not in st.session_state:
    st.session_state.last_query = ""


def targets_now():
    if st.session_state.custom_targets is not None:
        return st.session_state.custom_targets.copy()
    return {c: float(v) for c, v in GOALS[st.session_state.goal].items()}


def safe_value(food, nutrient):
    value = food.get(nutrient)
    try:
        if value is None or pd.isna(value):
            return float("nan")
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def portion_options(food_name):
    """Return approximate household measures matched to the food name."""
    name = str(food_name).lower()
    # Conversions are practical estimates, not exact weights; USDA nutrients remain per 100 g.
    if any(x in name for x in ["egg", "banana", "apple", "orange", "pear", "potato", "tomato"]):
        piece_weight = 50.0 if "egg" in name else 118.0 if "banana" in name else 182.0 if "apple" in name else 130.0 if "orange" in name else 178.0 if "pear" in name else 150.0 if "potato" in name else 120.0
        return {"gram (g)": 1.0, "piece / medium item (approx.)": piece_weight}
    if any(x in name for x in ["milk", "yogurt", "yoghurt", "juice", "smoothie", "soup", "water"]):
        return {"millilitre (ml)": 1.0, "small glass (200 ml)": 200.0, "cup (240 ml)": 240.0}
    if any(x in name for x in ["rice", "lentil", "dal", "beans", "chickpea", "chana", "oatmeal", "porridge", "pasta", "noodle", "quinoa"]):
        return {"gram (g)": 1.0, "small bowl (150 g cooked, approx.)": 150.0, "cup (180 g cooked, approx.)": 180.0, "half cup (90 g cooked, approx.)": 90.0}
    if any(x in name for x in ["bread", "toast", "roti", "chapati", "tortilla", "slice"]):
        return {"gram (g)": 1.0, "slice / medium roti (approx.)": 30.0}
    if any(x in name for x in ["peanut butter", "butter", "oil", "seeds", "nuts", "almond", "peanut", "walnut", "cashew"]):
        return {"gram (g)": 1.0, "tablespoon (approx. 15 g)": 15.0, "handful (approx. 30 g)": 30.0}
    return {"gram (g)": 1.0, "small serving (approx. 100 g)": 100.0, "medium serving (approx. 150 g)": 150.0, "large serving (approx. 200 g)": 200.0}


def portion_label(amount, unit):
    return f"{amount:g} × {unit}" if unit != "gram (g)" else f"{amount:g} g"


def add_item(food, meal, portion, measure_amount=None, measure_unit="gram (g)"):
    st.session_state.item_id += 1
    snapshot = {c: safe_value(food, c) for c in NUTRIENTS}
    st.session_state.meal_plan[meal].append({
        "item_id": st.session_state.item_id,
        "food_code": str(food.get("food_code", "USDA-UNKNOWN")),
        "food_name": str(food.get("food_name", "Unnamed food")),
        "portion_g": float(portion),
        "measure_amount": float(measure_amount if measure_amount is not None else portion),
        "measure_unit": str(measure_unit),
        "portion_label": portion_label(float(measure_amount if measure_amount is not None else portion), str(measure_unit)),
        "source": str(food.get("source", "USDA FoodData Central")),
        "nutrients_per_100g": snapshot,
        "data_type": str(food.get("data_type", "USDA record")),
    })


def meal_totals(items):
    totals = {c: 0.0 for c in NUTRIENTS}
    unknown = set()
    for item in items:
        snapshot = item.get("nutrients_per_100g", {})
        for c in NUTRIENTS:
            value = snapshot.get(c)
            if value is None or pd.isna(value):
                unknown.add(c)
            else:
                totals[c] += float(value) * float(item["portion_g"]) / 100
    for c in unknown:
        totals[c] = float("nan")
    return totals


def daily_totals():
    total = {c: 0.0 for c in NUTRIENTS}
    unknown = set()
    for meal in MEALS:
        for c, value in meal_totals(st.session_state.meal_plan[meal]).items():
            if pd.isna(value):
                unknown.add(c)
            else:
                total[c] += value
    for c in unknown:
        total[c] = float("nan")
    return total


def fmt(value, nutrient):
    if value is None or pd.isna(value):
        return "Unknown"
    return f"{value:.0f}" if nutrient == "energy_kj" else f"{value:.1f}"


def meal_export():
    rows = []
    for meal in MEALS:
        for item in st.session_state.meal_plan[meal]:
            row = {
                "meal": meal,
                "food_code": item["food_code"],
                "food_name": item["food_name"],
                "portion_g": item["portion_g"],
                "portion_measure": item.get("portion_label", f'{item["portion_g"]:.0f} g'),
                "source": item["source"],
                "data_type": item.get("data_type", ""),
            }
            for c in NUTRIENTS:
                value = item.get("nutrients_per_100g", {}).get(c)
                row[c] = (
                    float(value) * float(item["portion_g"]) / 100
                    if value is not None and pd.notna(value)
                    else float("nan")
                )
            rows.append(row)
    return pd.DataFrame(rows, columns=["meal", "food_code", "food_name", "portion_g", "portion_measure", "source", "data_type", *NUTRIENTS])


def recommend_from_global_results(results, daily, targets, goal, top_n=5):
    """Rank only foods returned by USDA search; never reads the local IFCT file."""
    if not results:
        return pd.DataFrame()
    weights = GOAL_WEIGHTS[goal]
    candidates = []
    for food in results:
        known = [(c, safe_value(food, c)) for c in NUTRIENTS]
        known = [(c, v) for c, v in known if pd.notna(v) and v >= 0]
        if not known:
            continue
        # Prioritize nutrient gaps. A missing daily total is not treated as zero.
        score = 0.0
        score_weight = 0.0
        for c, value_per_100g in known:
            current = daily.get(c, float("nan"))
            target = targets[c]
            if pd.isna(current) or target <= 0:
                continue
            gap = max(target - current, 0)
            if gap <= 0:
                continue
            contribution = min((value_per_100g / max(target, 1)) * 100, 100)
            score += contribution * weights.get(c, 0)
            score_weight += weights.get(c, 0)
        if score_weight <= 0:
            continue
        portion = 100.0
        # Suggest a portion up to 200 g to help address the most important known gap.
        weighted_gaps = []
        for c, value_per_100g in known:
            current = daily.get(c, float("nan"))
            if pd.notna(current) and targets[c] > current and value_per_100g > 0:
                weighted_gaps.append((weights.get(c, 0), (targets[c] - current) / value_per_100g * 100))
        if weighted_gaps:
            weighted_gaps.sort(reverse=True)
            portion = min(200.0, max(25.0, weighted_gaps[0][1]))
        row = {
            "food_code": food.get("food_code"),
            "food_name": food.get("food_name"),
            "source": food.get("source"),
            "data_type": food.get("data_type"),
            "suggested_portion_g": round(portion, 1),
            "recommendation_score": round(score / score_weight, 2),
        }
        for c in NUTRIENTS:
            v = safe_value(food, c)
            row[c] = v
            current = daily.get(c, float("nan"))
            row[f"projected_{c}"] = (
                current + v * portion / 100
                if pd.notna(current) and pd.notna(v)
                else float("nan")
            )
        candidates.append(row)
    if not candidates:
        return pd.DataFrame()
    return pd.DataFrame(candidates).sort_values("recommendation_score", ascending=False).head(top_n).reset_index(drop=True)


st.sidebar.title("🥗 AAHAR AI")
st.sidebar.caption("Global nutrition data • USDA FoodData Central")

# Step 1: collect user preferences and an additional-food budget.
if "food_preference" not in st.session_state:
    st.session_state.food_preference = "Vegetarian"
if "food_exclusions" not in st.session_state:
    st.session_state.food_exclusions = ""
if "budget_amount" not in st.session_state:
    st.session_state.budget_amount = 1000.0
if "budget_period" not in st.session_state:
    st.session_state.budget_period = "Month"

with st.sidebar.expander("Hostel profile & budget", expanded=True):
    st.caption("Budget is for extra food only; hostel mess fees are excluded.")
    food_preference = st.selectbox(
        "Food preference",
        ["Vegetarian", "Vegetarian with eggs", "Non-vegetarian"],
        key="food_preference",
    )
    food_exclusions = st.text_input(
        "Allergies / foods to avoid",
        key="food_exclusions",
        placeholder="e.g. peanuts, lactose",
        help="Enter allergies or foods you want the planner to exclude. This step records them; recommendation filtering is added next.",
    )
    budget_amount = st.number_input(
        "Additional food budget (₹)",
        min_value=0.0,
        max_value=100000.0,
        value=float(st.session_state.budget_amount),
        step=50.0,
        key="budget_amount",
    )
    budget_period = st.selectbox(
        "Budget period",
        ["Day", "Week", "Month"],
        key="budget_period",
    )
    period_days = {"Day": 1.0, "Week": 7.0, "Month": 30.0}[budget_period]
    daily_budget = budget_amount / period_days
    st.markdown("**Equivalent spending limits**")
    budget_cols = st.columns(3)
    budget_cols[0].metric("Per day", f"₹{daily_budget:.0f}")
    budget_cols[1].metric("Per week", f"₹{daily_budget * 7:.0f}")
    budget_cols[2].metric("Per 30 days", f"₹{daily_budget * 30:.0f}")
    st.caption("Monthly calculations use a 30-day planning month. Actual spending tracking will be added in a later step.")

goal = st.sidebar.selectbox("Dietary goal", list(GOALS), index=list(GOALS).index(st.session_state.goal))
if goal != st.session_state.goal:
    st.session_state.goal = goal
    st.session_state.custom_targets = None
st.sidebar.caption("Targets are illustrative defaults, not individualized medical advice.")
with st.sidebar.expander("Customize daily targets"):
    current_targets = targets_now()
    protein = st.number_input("Protein (g)", 0.0, 500.0, float(current_targets["protein_g"]), 5.0, key="protein_target")
    fibre = st.number_input("Fibre (g)", 0.0, 150.0, float(current_targets["fiber_total_g"]), 5.0, key="fibre_target")
    energy = st.number_input("Energy (kcal)", 0.0, 10000.0, float(current_targets["energy_kj"] / 4.184), 50.0, key="energy_target")
    carbs = st.number_input("Carbohydrates (g)", 0.0, 1000.0, float(current_targets["carbs_available_g"]), 10.0, key="carbs_target")
    fat = st.number_input("Fat (g)", 0.0, 500.0, float(current_targets["fat_g"]), 5.0, key="fat_target")
    if st.button("Apply custom targets"):
        st.session_state.custom_targets = {
            "protein_g": protein,
            "fiber_total_g": fibre,
            "energy_kj": energy * 4.184,
            "carbs_available_g": carbs,
            "fat_g": fat,
        }
        st.rerun()
    if st.button("Reset profile targets"):
        st.session_state.custom_targets = None
        st.rerun()

st.markdown("""<div class="aahar-hero"><h1>🥗 AAHAR AI</h1><p>Your food. Your goals. Your nutrition — made practical for hostel life.</p></div>""", unsafe_allow_html=True)
st.write("Search global food records, measure portions in familiar household units, plan meals, and track nutrition.")
st.caption(f"Profile: {food_preference} • Extra-food budget: ₹{budget_amount:.0f} per {budget_period.lower()}")
st.info("This version uses external USDA search results only. The local IFCT CSV is not loaded or used for food search or recommendations. USDA coverage of Indian foods varies.")
st.caption("Nutrient values are per 100 g when provided by USDA. Missing values remain unknown rather than being treated as zero.")
st.divider()

# Global food search
st.header("1. Search global food database")
st.write("Examples: banana, cooked lentils, oats, egg, tofu, brown rice, yogurt.")
has_key = bool(os.getenv("USDA_FDC_API_KEY"))
try:
    has_key = has_key or bool(st.secrets.get("USDA_FDC_API_KEY", ""))
except Exception:
    pass
if not has_key:
    st.warning("USDA API key not found. Add USDA_FDC_API_KEY to .streamlit/secrets.toml or set it as an environment variable.")

with st.form("global_search_form"):
    query = st.text_input("Food to search", placeholder="e.g. cooked lentils")
    do_search = st.form_submit_button("Search global database", type="primary")
if do_search:
    try:
        with st.spinner("Searching USDA FoodData Central..."):
            st.session_state.live_results = search_foods(query)
            st.session_state.last_query = query.strip()
        if not st.session_state.live_results:
            st.info("No matching foods found. Try a different search term.")
    except (NutritionAPIError, ValueError) as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Unexpected search error: {exc}")

results = st.session_state.live_results
if results:
    st.caption(f'{len(results)} results for "{st.session_state.last_query}" • Source: USDA FoodData Central')
    display_rows = []
    for food in results:
        row = {"Food": food["food_name"], "Data type": food.get("data_type", ""), "FDC ID": food.get("source_id")}
        row.update({LABELS[c]: food.get(c) for c in NUTRIENTS})
        display_rows.append(row)
    st.dataframe(pd.DataFrame(display_rows), hide_index=True, use_container_width=True)

    labels = [f'{food["food_name"]} — ID {food.get("source_id")} ({food.get("data_type", "USDA")})' for food in results]
    choice = st.selectbox("Choose a food record", labels, key="global_food_choice")
    selected = results[labels.index(choice)]
    with st.expander("Selected global record details"):
        st.write(f"**Source:** {selected.get('source', 'USDA FoodData Central')}")
        st.write(f"**FDC ID:** {selected.get('source_id')}")
        st.write(f"**Data type:** {selected.get('data_type')}")
        st.write("Values depend on the USDA record and may vary by preparation and food form.")
    st.markdown("#### Choose a familiar portion")
    measures = portion_options(selected["food_name"])
    m1, m2, m3 = st.columns([2, 1, 2])
    with m1:
        measure_unit = st.selectbox("How do you measure it?", list(measures), key="global_measure_unit")
    with m2:
        measure_amount = st.number_input("Quantity", min_value=0.25, max_value=20.0, value=1.0, step=0.25, key="global_measure_amount")
    with m3:
        selected_meal = st.selectbox("Add to meal", MEALS, index=3, key="global_add_meal")
    grams_per_unit = measures[measure_unit]
    selected_portion = float(measure_amount) * grams_per_unit
    st.caption(f"Estimated serving weight: **{selected_portion:.0f} g**. Household measures vary by food, size and preparation; adjust if you know the actual weight.")
    if st.button("＋ Add food to meal plan", type="primary", key="add_global_food"):
        add_item(selected, selected_meal, selected_portion, measure_amount, measure_unit)
        st.success(f"Added {portion_label(measure_amount, measure_unit)} of {selected['food_name']}.")
        st.rerun()

st.divider()
st.header("2. Your meal plan")
for meal in MEALS:
    items = st.session_state.meal_plan[meal]
    totals = meal_totals(items)
    with st.expander(f"{meal} — {len(items)} item(s)", expanded=(meal == "Breakfast")):
        if not items:
            st.caption("No foods added yet. Search the global database above to add a food.")
            continue
        for item in items:
            c1, c2, c3, c4 = st.columns([3, 1, 2, 1])
            c1.write(f"**{item['food_name']}**")
            c1.caption(item["food_code"])
            c2.write(item.get("portion_label", f"{item['portion_g']:.0f} g"))
            c2.caption(f"≈ {item['portion_g']:.0f} g")
            c3.caption(item.get("source", "USDA FoodData Central"))
            if c4.button("Remove", key=f"remove_{meal}_{item['item_id']}"):
                st.session_state.meal_plan[meal] = [x for x in items if x["item_id"] != item["item_id"]]
                st.rerun()
        st.dataframe(
            pd.DataFrame([{"Nutrient": LABELS[c], "Amount": fmt(totals[c], c)} for c in NUTRIENTS]),
            hide_index=True,
            use_container_width=True,
        )

st.divider()
st.header("3. Daily nutrition dashboard")
daily = daily_totals()
targets = targets_now()
metrics = st.columns(5)
for i, nutrient in enumerate(NUTRIENTS):
    amount = daily[nutrient]
    metrics[i].metric(
        LABELS[nutrient],
        fmt(amount, nutrient),
        delta=None if pd.isna(amount) else f"{amount - targets[nutrient]:+.1f}",
    )

st.subheader("Progress against targets")
progress_rows = []
for nutrient in NUTRIENTS:
    amount, target = daily[nutrient], targets[nutrient]
    pct = amount / target * 100 if pd.notna(amount) and target > 0 else float("nan")
    progress_rows.append({
        "Nutrient": LABELS[nutrient],
        "Consumed": amount,
        "Target": target,
        "Remaining": max(target - amount, 0) if pd.notna(amount) else float("nan"),
        "Progress (%)": pct,
    })
    st.write(f"**{LABELS[nutrient]}**")
    if pd.isna(pct):
        st.caption("Progress unavailable: intake is unknown or target is zero.")
    else:
        st.progress(min(max(pct / 100, 0), 1))
        st.caption(f"{pct:.1f}% of target")
with st.expander("View nutrition table"):
    st.dataframe(pd.DataFrame(progress_rows), hide_index=True, use_container_width=True)

st.divider()
st.header("4. Recommendations from global results")
st.caption("Recommendations are ranked from your latest USDA search. Budget and food preferences are collected in the sidebar; applying them to recommendation filtering and cost optimization is the next implementation step.")
recommendations = recommend_from_global_results(results, daily, targets, st.session_state.goal)
if recommendations.empty:
    st.info("Search a food above first. Recommendations can only use the global records returned by your latest search and known nutrient gaps.")
else:
    show = recommendations.rename(columns={
        "food_name": "Food",
        "source": "Source",
        "data_type": "Data type",
        "suggested_portion_g": "Suggested portion (g)",
        "recommendation_score": "Recommendation score",
        "protein_g": "Protein (g/100 g)",
        "fiber_total_g": "Fibre (g/100 g)",
        "energy_kj": "Energy (kJ/100 g)",
        "carbs_available_g": "Carbohydrates (g/100 g)",
        "fat_g": "Fat (g/100 g)",
    })
    st.dataframe(show, hide_index=True, use_container_width=True)
    rec_labels = [
        f'{row["food_name"]} — {row["suggested_portion_g"]:.0f} g'
        for _, row in recommendations.iterrows()
    ]
    rec_choice = st.selectbox("Choose a recommended global food", rec_labels, key="global_rec_choice")
    rec = recommendations.iloc[rec_labels.index(rec_choice)]
    rec_meal = st.selectbox("Meal for recommended food", MEALS, index=3, key="global_rec_meal")
    if st.button("Add recommended global food", key="add_global_rec"):
        found = next((f for f in results if str(f.get("food_code")) == str(rec["food_code"])), None)
        if found:
            add_item(found, rec_meal, float(rec["suggested_portion_g"]))
            st.success("Added recommended USDA food to your meal plan.")
            st.rerun()
    with st.expander("Projected totals for recommendations"):
        projected_rows = []
        for _, row in recommendations.iterrows():
            projected = {"Food": row["food_name"], "Portion (g)": row["suggested_portion_g"]}
            for nutrient in NUTRIENTS:
                projected[f"Projected {LABELS[nutrient]}"] = row.get(f"projected_{nutrient}", float("nan"))
            projected_rows.append(projected)
        st.dataframe(pd.DataFrame(projected_rows), hide_index=True, use_container_width=True)

st.divider()
st.header("5. Export reports")
c1, c2 = st.columns(2)
with c1:
    st.download_button(
        "Download meal plan CSV",
        meal_export().to_csv(index=False).encode("utf-8"),
        "aahar_meal_plan.csv",
        "text/csv",
        key="meal_csv",
        use_container_width=True,
    )
with c2:
    summary = pd.DataFrame([{
        "nutrient": LABELS[c],
        "consumed": daily[c],
        "target": targets[c],
        "remaining_to_target": max(targets[c] - daily[c], 0) if pd.notna(daily[c]) else float("nan"),
        "unit": "kJ" if c == "energy_kj" else "g",
    } for c in NUTRIENTS])
    st.download_button(
        "Download daily summary CSV",
        summary.to_csv(index=False).encode("utf-8"),
        "aahar_daily_nutrition.csv",
        "text/csv",
        key="summary_csv",
        use_container_width=True,
    )

with st.expander("Reset meal plan"):
    st.warning("This removes all items from all meals.")
    if st.button("Clear all meals", key="clear_meals"):
        st.session_state.meal_plan = {meal: [] for meal in MEALS}
        st.rerun()

st.divider()
st.caption("AAHAR AI is an educational prototype, not medical advice. USDA coverage varies; values depend on record type and preparation. This app does not load the local IFCT CSV.")
