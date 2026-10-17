"""USDA FoodData Central live lookup. IFCT remains the primary local source."""
import os
import requests

BASE_URL = "https://api.nal.usda.gov/fdc/v1"
TIMEOUT_SECONDS = 15
NUTRIENT_IDS = {
    "protein_g": 1003,
    "fat_g": 1004,
    "carbs_available_g": 1005,
    "fiber_total_g": 1079,
    "energy_kj": 1008,
}


class NutritionAPIError(RuntimeError):
    """User-friendly live API error."""


def get_api_key(api_key=None):
    key = api_key or os.getenv("USDA_FDC_API_KEY")
    if not key:
        # Support Streamlit secrets without requiring Streamlit for unit tests.
        try:
            import streamlit as st
            key = st.secrets.get("USDA_FDC_API_KEY", "")
        except Exception:
            key = ""
    if not key:
        raise NutritionAPIError(
            "USDA API key missing. Set USDA_FDC_API_KEY or add it to "
            ".streamlit/secrets.toml."
        )
    return key.strip()


def _request_json(url, params, api_key):
    params = {**params, "api_key": api_key}
    try:
        response = requests.get(
            url, params=params, timeout=TIMEOUT_SECONDS,
            headers={"User-Agent": "AAHAR-AI/1.0"},
        )
    except requests.RequestException as exc:
        raise NutritionAPIError(
            "Could not connect to USDA. Check your internet connection."
        ) from exc
    if response.status_code == 429:
        raise NutritionAPIError("USDA rate limit reached. Wait and try again.")
    if response.status_code in (401, 403):
        raise NutritionAPIError("USDA rejected the API key. Check your key.")
    if response.status_code >= 400:
        raise NutritionAPIError(f"USDA API returned HTTP {response.status_code}.")
    try:
        return response.json()
    except ValueError as exc:
        raise NutritionAPIError("USDA returned invalid JSON.") from exc


def _nutrients(raw):
    result = {key: None for key in NUTRIENT_IDS}
    for item in raw or []:
        nutrient = item.get("nutrient") if isinstance(item.get("nutrient"), dict) else item
        nid = nutrient.get("id", nutrient.get("nutrientId"))
        name = str(nutrient.get("name", item.get("nutrientName", ""))).lower()
        try:
            value = float(item.get("amount", item.get("value")))
        except (TypeError, ValueError):
            continue
        target = next((key for key, known_id in NUTRIENT_IDS.items()
                       if str(nid) == str(known_id)), None)
        if target is None:
            aliases = {
                "protein_g": ("protein",),
                "fat_g": ("total lipid", "total fat"),
                "carbs_available_g": ("carbohydrate, by difference", "carbohydrate"),
                "fiber_total_g": ("fiber, total dietary", "dietary fiber"),
                "energy_kj": ("energy",),
            }
            target = next((key for key, terms in aliases.items()
                           if any(term in name for term in terms)), None)
        if target is None or result[target] is not None:
            continue
        unit = str(nutrient.get("unitName", item.get("unitName", ""))).lower()
        if target == "energy_kj":
            if unit in ("kcal", "kcalories") or not unit:
                value *= 4.184
        result[target] = value
    return result


def normalize_search_result(food):
    fdc_id = food.get("fdcId")
    data_type = str(food.get("dataType") or "USDA FoodData Central")
    return {
        "food_code": f"USDA-{fdc_id}" if fdc_id is not None else "USDA-UNKNOWN",
        "food_name": str(food.get("description") or "Unnamed food").strip(),
        "source": f"USDA FoodData Central ({data_type})",
        "source_id": fdc_id,
        "data_type": data_type,
        **_nutrients(food.get("foodNutrients")),
    }


def search_foods(query, api_key=None, page_size=10):
    query = (query or "").strip()
    if len(query) < 2:
        raise ValueError("Enter at least 2 characters to search.")
    if not isinstance(page_size, int) or isinstance(page_size, bool) or not 1 <= page_size <= 25:
        raise ValueError("page_size must be an integer from 1 to 25.")
    payload = _request_json(
        f"{BASE_URL}/foods/search",
        {
            "query": query,
            "pageSize": page_size,
            "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"],
        },
        get_api_key(api_key),
    )
    return [normalize_search_result(x) for x in payload.get("foods", [])]


def get_food_details(fdc_id, api_key=None):
    try:
        fdc_id = int(fdc_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("FDC ID must be an integer.") from exc
    payload = _request_json(
        f"{BASE_URL}/food/{fdc_id}", {}, get_api_key(api_key)
    )
    return {
        "food_code": f"USDA-{fdc_id}",
        "food_name": str(payload.get("description") or "Unnamed food"),
        "source": f"USDA FoodData Central ({payload.get('dataType', 'USDA')})",
        "source_id": fdc_id,
        "data_type": payload.get("dataType", "USDA"),
        **_nutrients(payload.get("foodNutrients")),
    }
