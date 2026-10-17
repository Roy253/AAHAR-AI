
from pathlib import Path
import pandas as pd

CSV_PATH = Path("data/processed/ifct_page50_structured.csv")

EXPECTED_E017 = {
    "food_name": "Dates, dry, pale brown (Phoenix dactylifera)",
    "moisture_g": "11.14±0.73",
    "protein_g": "2.45±0.24",
    "ash_g": "2.20±0.07",
    "fat_g": "0.35±0.03",
    "fiber_total_g": "8.95±0.23",
    "fiber_insoluble_g": "7.53±0.22",
    "fiber_soluble_g": "1.42±0.14",
    "carbs_available_g": "74.91±0.52",
    "energy_kj": "1340±12",
}


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV not found: {CSV_PATH}. Run the parsing script first."
        )

    df = pd.read_csv(CSV_PATH, dtype=str)
    matches = df[df["food_code"] == "E017"]

    if len(matches) != 1:
        print(f"Expected exactly one E017 record; found {len(matches)}.")
        return

    row = matches.iloc[0]
    print("AAHAR AI - E017 SOURCE CHECK")
    print(f"Food: {row['food_name']}")

    failures = []

    for column, expected in EXPECTED_E017.items():
        actual = str(row[column]).strip()
        passed = actual == expected

        print(
            f"{'PASS' if passed else 'CHECK'} | "
            f"{column}: actual={actual!r}, expected={expected!r}"
        )

        if not passed:
            failures.append(column)

    print()
    if failures:
        print("Review required for:", ", ".join(failures))
        print("Do not use this row for recommendations until checked.")
    else:
        print("All E017 fields match the expected source values.")


if __name__ == "__main__":
    main()
