
from pathlib import Path
import pandas as pd

CSV_PATH = Path("data/processed/ifct_page50_structured.csv")

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
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH, dtype=str)

    print("=" * 55)
    print("AAHAR AI - DATASET QUALITY CHECK")
    print("=" * 55)

    # 1. Schema validation
    missing_columns = [
        col for col in REQUIRED_COLUMNS if col not in df.columns
    ]
    print(f"\nRows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Missing required columns: {missing_columns}")

    if missing_columns:
        print("STOP: Dataset schema is incomplete.")
        return

    # 2. Duplicate checks
    duplicate_codes = df[df["food_code"].duplicated(keep=False)]
    print(f"Duplicate food codes: {len(duplicate_codes)}")

    # 3. Empty-value checks
    empty_cells = (
        df[REQUIRED_COLUMNS]
        .replace(r"^\s*$", pd.NA, regex=True)
        .isna()
        .sum()
    )
    print("\nEmpty values:")
    print(empty_cells[empty_cells > 0].to_string() or "None")

    # 4. Display a small review sample
    print("\nFirst five foods:")
    print(
        df[["food_code", "food_name", "protein_g", "energy_kj"]]
        .head()
        .to_string(index=False)
    )

    # 5. Show the source page distribution
    print("\nSource pages:")
    print(df["source_pdf_page"].value_counts().to_string())

    print("\nQuality check completed.")
    print("Note: structural checks do not prove every nutrient is aligned.")

if __name__ == "__main__":
    main()
