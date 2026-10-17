
from pathlib import Path

import pandas as pd
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
CSV_PATH = Path("data/processed/ifct_pages52_55_candidate.csv")

FOOD_CODES = ["E059", "E060", "E061", "E062", "E063"]


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(PDF_PATH)

    if not CSV_PATH.exists():
        raise FileNotFoundError(CSV_PATH)

    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")

    with pdfplumber.open(PDF_PATH) as pdf:
        for code in FOOD_CODES:
            rows = df[df["food_code"] == code]

            if rows.empty:
                print(f"\n{code}: NOT FOUND IN CSV")
                continue

            row = rows.iloc[0]
            page_number = int(row["source_pdf_page"])

            page = pdf.pages[page_number - 1]
            text = page.extract_text() or ""

            print("\n" + "=" * 70)
            print(f"{code} | CSV page {page_number}")
            print("=" * 70)

            print("\nCSV values:")
            print(row.to_string())

            print("\nOriginal PDF text around food code:")
            lines = text.splitlines()

            matches = [
                i for i, line in enumerate(lines)
                if code in line
            ]

            if not matches:
                print("Food code not found in extracted PDF text.")
                continue

            for i in matches:
                start = max(0, i - 1)
                end = min(len(lines), i + 3)

                for line in lines[start:end]:
                    print(line)

                print("-" * 40)


if __name__ == "__main__":
    main()
