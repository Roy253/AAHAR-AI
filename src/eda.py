
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# AAHAR AI — EXPLORATORY DATA ANALYSIS
# ============================================================

DATA_PATH = Path("data/processed/ifct_foods_clean.csv")
REPORT_DIR = Path("reports")
FIGURE_DIR = REPORT_DIR / "figures"

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
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}. Run preprocessing first."
        )

    df = pd.read_csv(DATA_PATH)

    missing_columns = [
        col for col in ["food_code", "food_name", *NUTRIENTS]
        if col not in df.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    # Summary statistics
    summary = df[NUTRIENTS].describe().T
    summary["missing_count"] = df[NUTRIENTS].isna().sum()
    summary.to_csv(REPORT_DIR / "nutrient_summary.csv")

    # Missing values
    missing = df[NUTRIENTS].isna().sum().rename("missing_count")
    missing.to_csv(REPORT_DIR / "nutrient_missing_values.csv")

    # Nutrient distributions
    for nutrient in NUTRIENTS:
        values = df[nutrient].dropna()

        if values.empty:
            print(f"Skipping {nutrient}: no numeric values.")
            continue

        plt.figure(figsize=(8, 5))
        plt.hist(values, bins=20, edgecolor="black")
        plt.title(f"Distribution of {nutrient}")
        plt.xlabel(nutrient)
        plt.ylabel("Number of foods")
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / f"{nutrient}_distribution.png")
        plt.close()

    # Correlation between nutrients
    correlation = df[NUTRIENTS].corr()
    correlation.to_csv(REPORT_DIR / "nutrient_correlations.csv")

    plt.figure(figsize=(10, 8))
    image = plt.imshow(correlation, aspect="auto", vmin=-1, vmax=1)
    plt.colorbar(image, label="Correlation")
    plt.xticks(range(len(NUTRIENTS)), NUTRIENTS, rotation=90)
    plt.yticks(range(len(NUTRIENTS)), NUTRIENTS)
    plt.title("Nutrient Correlation Matrix")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "nutrient_correlation_matrix.png")
    plt.close()

    print("=" * 50)
    print("AAHAR AI — EDA COMPLETED")
    print("=" * 50)
    print(f"Food records: {len(df)}")
    print(f"Unique food codes: {df['food_code'].nunique()}")
    print(f"Summary: {REPORT_DIR / 'nutrient_summary.csv'}")
    print(f"Missing values: {REPORT_DIR / 'nutrient_missing_values.csv'}")
    print(f"Correlations: {REPORT_DIR / 'nutrient_correlations.csv'}")
    print(f"Charts: {FIGURE_DIR}")


if __name__ == "__main__":
    main()
