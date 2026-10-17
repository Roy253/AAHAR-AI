
from pathlib import Path
import pandas as pd
import pdfplumber

PDF = Path("data/source_docs/IFCT2017_16122024.pdf")
CSV = Path("data/processed/ifct_pages52_55_candidate.csv")

CODES = ["E059", "E060", "E061", "E062", "E063"]

def main():
    df = pd.read_csv(CSV, dtype=str).fillna("")
    columns = [
        "moisture_g", "protein_g", "ash_g", "fat_g",
        "fiber_total_g", "fiber_insoluble_g", "fiber_soluble_g",
        "carbs_available_g", "energy_kj",
    ]

    with pdfplumber.open(PDF) as pdf:
        for code in CODES:
            row = df.loc[df["food_code"] == code]

            if len(row) != 1:
                print(f"{code}: FAIL — expected one CSV row")
                continue

            row = row.iloc[0]
            page = pdf.pages[int(row["source_pdf_page"]) - 1]
            text = page.extract_text() or ""

            matching_lines = [
                line for line in text.splitlines()
                if code in line
            ]

            source_text = " ".join(matching_lines)
            missing_values = [
                col for col in columns
                if row[col] and row[col] not in source_text
            ]

            print(
                f"{code}: "
                f"{'PASS' if not missing_values else 'REVIEW'}"
            )
            if missing_values:
                print("  Values not found:", missing_values)
            print("  Source row:", source_text[:300])

if __name__ == "__main__":
    main()
