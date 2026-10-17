
from pathlib import Path
import pandas as pd

SOURCE = Path("data/processed/ifct_page50_recovered.csv")
DESTINATION = Path("data/processed/ifct_page50_checkpoint.csv")

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
    if not SOURCE.exists():
        raise FileNotFoundError(f"Recovered dataset not found: {SOURCE}")

    df = pd.read_csv(SOURCE, dtype=str)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if df["food_code"].duplicated().any():
        raise ValueError("Duplicate food codes detected.")

    if len(df) != 21:
        raise ValueError(f"Expected 21 records, found {len(df)}.")

    lemon = df[df["food_code"] == "E033"]
    if len(lemon) != 1:
        raise ValueError("Expected exactly one E033 record.")

    # Verify the known blank dietary-fibre fields.
    fibre_columns = [
        "fiber_total_g",
        "fiber_insoluble_g",
        "fiber_soluble_g",
    ]
    if lemon[fibre_columns].notna().any(axis=None):
        raise ValueError("E033 fibre fields should remain blank.")

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DESTINATION, index=False, encoding="utf-8-sig")

    print("Checkpoint created successfully.")
    print(f"Records: {len(df)}")
    print(f"Saved to: {DESTINATION}")


if __name__ == "__main__":
    main()
