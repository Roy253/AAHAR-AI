
from pathlib import Path
import pandas as pd

SOURCE = Path("data/processed/ifct_pages50_51_candidate.csv")
OUTPUT = Path("data/processed/ifct_pages50_51_reviewed.csv")
AUDIT = Path("reports/e033_correction_audit.csv")

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

def main():
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    df = pd.read_csv(SOURCE, dtype=str).fillna("")

    # E033 must be absent from the candidate file before adding it.
    if (df["food_code"] == "E033").any():
        raise ValueError(
            "E033 already exists in the candidate file. "
            "Stop to avoid creating a duplicate."
        )

    e033 = {
        "food_code": "E033",
        "food_name": "Lemon, juice (Citrus limon)",
        "regions_count": "6",
        "source_pdf_page": "50",
        "moisture_g": "91.59±0.53",
        "protein_g": "0.41±0.05",
        "ash_g": "0.28±0.03",
        "fat_g": "0.75±0.02",
        "fiber_total_g": "",
        "fiber_insoluble_g": "",
        "fiber_soluble_g": "",
        "carbs_available_g": "6.97±0.56",
        "energy_kj": "153±9",
    }

    # Preserve the dataset's existing schema and column order.
    for col in df.columns:
        if col not in e033:
            e033[col] = ""

    df = pd.concat(
        [df, pd.DataFrame([e033], columns=df.columns)],
        ignore_index=True,
    )

    if df["food_code"].duplicated().any():
        raise ValueError("Duplicate food codes detected.")

    if len(df) != 42:
        raise ValueError(f"Expected 42 records, found {len(df)}.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    audit = pd.DataFrame([{
        "food_code": "E033",
        "source_pdf_page": 50,
        "status": "MAPPED_FROM_VISIBLE_SOURCE_POSITIONS",
        "blank_fields": (
            "fiber_total_g;fiber_insoluble_g;fiber_soluble_g"
        ),
        "note": (
            "Values mapped using the visible PDF row positions; "
            "confirm against the original table before production use."
        ),
    }])

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(AUDIT, index=False, encoding="utf-8-sig")

    print("E033 mapping applied.")
    print(f"Rows: {len(df)}")
    print(f"Unique food codes: {df['food_code'].nunique()}")
    print(f"Reviewed dataset: {OUTPUT}")
    print(f"Audit report: {AUDIT}")

if __name__ == "__main__":
    main()
