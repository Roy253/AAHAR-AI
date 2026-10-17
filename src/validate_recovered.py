
from pathlib import Path
import pandas as pd

CSV_PATH = Path("data/processed/ifct_page50_recovered.csv")

REQUIRED_COLUMNS = [
    "food_code",
    "food_name",
    "regions_count",
    "source_pdf_page",
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


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(CSV_PATH)

    df = pd.read_csv(CSV_PATH, dtype=str)

    print("=" * 55)
    print("AAHAR AI - RECOVERED DATA VALIDATION")
    print("=" * 55)
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Missing required columns: "
          f"{[c for c in REQUIRED_COLUMNS if c not in df.columns]}")
    print(f"Duplicate food codes: {df['food_code'].duplicated().sum()}")

    print("\nRecords E032-E035:")
    columns = [
        "food_code",
        "food_name",
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
    print(
        df[df["food_code"].isin(["E032", "E033", "E034", "E035"])][columns]
        .to_string(index=False)
    )

    print("\nBlank nutrient cells by column:")
    print(df[REQUIRED_COLUMNS[4:]].isna().sum().to_string())

    print("\nValidation complete.")
    print("This checks structure, not full source accuracy.")


if __name__ == "__main__":
    main()
