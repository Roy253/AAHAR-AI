
from pathlib import Path
import pandas as pd

DATASET = Path("data/processed/ifct_pages50_55_consolidated.csv")

NUTRIENTS = [
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
    if not DATASET.exists():
        raise FileNotFoundError(DATASET)

    df = pd.read_csv(DATASET, dtype=str).fillna("")

    print("AAHAR AI — CONSOLIDATED DATASET CHECK")
    print("=" * 48)
    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("Unique food codes:", df["food_code"].nunique())
    print("Duplicate food codes:", df["food_code"].duplicated().sum())

    print("\nRecords by PDF page:")
    print(df.groupby("source_pdf_page").size().to_string())

    print("\nMissing values:")
    for col in ["food_name"] + NUTRIENTS:
        print(f"{col}: {(df[col].str.strip() == '').sum()}")

    print("\nNutrient fields that cannot be parsed:")
    for col in NUTRIENTS:
        numeric = pd.to_numeric(
            df[col].str.replace(r"±.*$", "", regex=True),
            errors="coerce",
        )
        invalid = df[col].ne("") & numeric.isna()
        print(f"{col}: {int(invalid.sum())}")

    print("\nFirst five records:")
    print(
        df[["food_code", "food_name", "source_pdf_page"]]
        .head()
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()

