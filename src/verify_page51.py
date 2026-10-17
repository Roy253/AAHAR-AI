
from pathlib import Path
import pandas as pd

CANDIDATE = Path("data/processed/ifct_page51_candidate.csv")
OUTPUT = Path("reports/ifct_page51_verification.csv")

EXPECTED_FIRST = {
    "food_name": "Mango, ripe, himsagar (Mangifera indica)",
    "regions_count": "3",
    "moisture_g": "88.04±0.10",
    "protein_g": "0.46±0.04",
    "ash_g": "0.38±0.02",
    "fat_g": "0.54±0.02",
    "fiber_total_g": "1.55±0.13",
    "fiber_insoluble_g": "0.82±0.19",
    "fiber_soluble_g": "0.73±0.06",
    "carbs_available_g": "9.03±0.26",
    "energy_kj": "187±5",
}


def main():
    df = pd.read_csv(CANDIDATE, dtype=str).fillna("")

    if len(df) != 21:
        raise ValueError(f"Expected 21 rows; found {len(df)}")

    if df["food_code"].duplicated().any():
        raise ValueError("Duplicate food codes found.")

    row = df.loc[df["food_code"] == "E038"]

    if len(row) != 1:
        raise ValueError("Expected exactly one E038 record.")

    row = row.iloc[0]
    checks = []

    for column, expected in EXPECTED_FIRST.items():
        actual = row[column]
        checks.append({
            "food_code": "E038",
            "field": column,
            "expected": expected,
            "actual": actual,
            "match": actual == expected,
        })

    result = pd.DataFrame(checks)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)

    print("Page-51 verification")
    print(f"Rows: {len(df)}")
    print(f"Unique food codes: {df['food_code'].nunique()}")
    print(f"E038 fields matching: {result['match'].sum()}/{len(result)}")
    print(f"Report: {OUTPUT}")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
