
from pathlib import Path
import re
import csv
import pdfplumber
import argparse

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
OUTPUT_DIR = Path("data/processed")

FOOD_CODE_PATTERN = re.compile(r"^[A-Z]\d{3}$")

# Confirmed from the page-51 source table and E038 coordinates.
REGION_X_MIN = 260
REGION_X_MAX = 300
NUTRIENT_X_MIN = 300

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


def extract_page(page_number):
    records = []
    review = []

    with pdfplumber.open(PDF_PATH) as pdf:
        if page_number < 1 or page_number > len(pdf.pages):
            raise ValueError(f"Invalid PDF page: {page_number}")

        page = pdf.pages[page_number - 1]
        words = page.extract_words()

    code_words = [
        w for w in words
        if FOOD_CODE_PATTERN.fullmatch(w["text"])
    ]

    for code_word in code_words:
        y = code_word["top"]

        row_words = sorted(
            [w for w in words if abs(w["top"] - y) <= 3],
            key=lambda w: w["x0"],
        )

        region_words = [
            w for w in row_words
            if REGION_X_MIN <= w["x0"] < REGION_X_MAX
        ]

        nutrient_words = [
            w for w in row_words
            if w["x0"] >= NUTRIENT_X_MIN
        ]

        if len(region_words) != 1:
            review.append({
                "food_code": code_word["text"],
                "reason": f"Expected one region count, found {len(region_words)}",
                "source_pdf_page": page_number,
            })
            continue

        values = [w["text"] for w in nutrient_words]

        if len(values) != 9:
            review.append({
                "food_code": code_word["text"],
                "reason": f"Expected 9 nutrient values, found {len(values)}",
                "source_pdf_page": page_number,
            })
            continue

        # Name is between the food code and region-count column.
        name_words = [
            w["text"] for w in row_words
            if code_word["x1"] < w["x0"] < REGION_X_MIN
        ]

        record = {
            "food_code": code_word["text"],
            "food_name": " ".join(name_words),
            "regions_count": region_words[0]["text"],
            "source_pdf_page": page_number,
        }

        record.update(dict(zip(NUTRIENT_COLUMNS, values)))
        records.append(record)

    return records, review


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", type=int, required=True)
    args = parser.parse_args()

    if not PDF_PATH.exists():
        raise FileNotFoundError(PDF_PATH)

    records, review = extract_page(args.page)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"ifct_page{args.page}_candidate.csv"
    review_file = OUTPUT_DIR / f"ifct_page{args.page}_review.csv"

    fields = [
        "food_code",
        "food_name",
        "regions_count",
        "source_pdf_page",
        *NUTRIENT_COLUMNS,
    ]

    with output_file.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    with review_file.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["food_code", "reason", "source_pdf_page"],
        )
        writer.writeheader()
        writer.writerows(review)

    print(f"PDF page: {args.page}")
    print(f"Candidate records: {len(records)}")
    print(f"Records requiring review: {len(review)}")
    print(f"Candidate CSV: {output_file}")
    print(f"Review CSV: {review_file}")


if __name__ == "__main__":
    main()
