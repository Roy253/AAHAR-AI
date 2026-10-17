
from pathlib import Path
import re

import pandas as pd


# ============================================================
# AAHAR AI — NUTRITION DATA PREPROCESSING
# ============================================================

INPUT_PATH = Path(
    "data/processed/ifct_pages50_55_consolidated.csv"
)
OUTPUT_PATH = Path(
    "data/processed/ifct_foods_clean.csv"
)
REPORT_PATH = Path(
    "reports/data_quality_report.csv"
)

NUTRIENT_COLUMNS = [
    "moisture_g",
    "protein_g",
    "ash_g",
    "fat_g",
    "fiber_total_g",
    "fiber_insoluble_g",
    "fiber_soluble_g",
    "carbs_available_g",
    "energy_kj",
]

REQUIRED_COLUMNS = [
    "food_code",
    "food_name",
    "regions_count",
    "source_pdf_page",
    *NUTRIENT_COLUMNS,
]


def parse_nutrient(value):
    """Convert an IFCT value or mean ± uncertainty to its mean."""
    if pd.isna(value):
        return float("nan")

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "null"}:
        return float("nan")

    # Accept decimal values and optional uncertainty, e.g. 11.20±0.49.
    pattern = r"^\s*(-?\d+(?:\.\d+)?)\s*(?:±|\+/-)\s*(-?\d+(?:\.\d+)?)?\s*$"
    match = re.match(pattern, text)

    if match:
        return float(match.group(1))

    # Also accept a plain numeric value.
    try:
        return float(text)
    except ValueError:
        return float("nan")


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_PATH}\n"
            "Verify that the consolidated CSV exists before continuing."
        )

    df = pd.read_csv(INPUT_PATH)

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Input dataset is missing columns: {missing_columns}"
        )

    original_rows = len(df)

    # Standardize text fields.
    df["food_code"] = df["food_code"].astype("string").str.strip()
    df["food_name"] = df["food_name"].astype("string").str.strip()

    # Keep the original nutrient strings for auditing.
    for column in NUTRIENT_COLUMNS:
        df[column] = df[column].map(parse_nutrient)

    # Convert metadata to numeric values where possible.
    df["regions_count"] = pd.to_numeric(
        df["regions_count"], errors="coerce"
    )
    df["source_pdf_page"] = pd.to_numeric(
        df["source_pdf_page"], errors="coerce"
    ).astype("Int64")

    # Detect duplicate food codes; do not silently remove records.
    duplicate_mask = df["food_code"].duplicated(keep=False)
    duplicate_count = int(duplicate_mask.sum())

    # Check required identifiers.
    missing_code_count = int(df["food_code"].isna().sum())
    missing_name_count = int(
        (df["food_name"].isna() | df["food_name"].eq("")).sum()
    )

    # Summarize missingness and invalid values.
    report_rows = []

    report_rows.append({
        "check": "total_rows",
        "column": "all",
        "count": original_rows,
        "status": "INFO",
    })
    report_rows.append({
        "check": "duplicate_food_code_rows",
        "column": "food_code",
        "count": duplicate_count,
        "status": "REVIEW" if duplicate_count else "PASS",
    })
    report_rows.append({
        "check": "missing_food_codes",
        "column": "food_code",
        "count": missing_code_count,
        "status": "REVIEW" if missing_code_count else "PASS",
    })
    report_rows.append({
        "check": "missing_food_names",
        "column": "food_name",
        "count": missing_name_count,
        "status": "REVIEW" if missing_name_count else "PASS",
    })

    for column in NUTRIENT_COLUMNS:
        missing_count = int(df[column].isna().sum())
        negative_count = int((df[column] < 0).sum())

        report_rows.append({
            "check": "missing_nutrient_values",
            "column": column,
            "count": missing_count,
            "status": "INFO" if missing_count else "PASS",
        })
        report_rows.append({
            "check": "negative_nutrient_values",
            "column": column,
            "count": negative_count,
            "status": "REVIEW" if negative_count else "PASS",
        })

    # Preserve questionable rows for manual review.
    # This script reports duplicates rather than choosing a winner.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_PATH, index=False)
    pd.DataFrame(report_rows).to_csv(REPORT_PATH, index=False)

    print("=" * 55)
    print("AAHAR AI — PREPROCESSING SUMMARY")
    print("=" * 55)
    print(f"Rows processed: {original_rows}")
    print(f"Duplicate-code rows requiring review: {duplicate_count}")
    print(f"Missing food codes: {missing_code_count}")
    print(f"Missing food names: {missing_name_count}")
    print(f"Cleaned dataset: {OUTPUT_PATH}")
    print(f"Quality report: {REPORT_PATH}")
    print("\nNote: missing nutrient values remain NaN.")
    print("Review the quality report before using this dataset.")


if __name__ == "__main__":
    main()
