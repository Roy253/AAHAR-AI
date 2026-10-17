
from pathlib import Path
import argparse
import csv
import re

import pandas as pd
import pdfplumber


# ============================================================
# AAHAR AI — IFCT BATCH EXTRACTION
# ============================================================

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
OUTPUT_DIR = Path("data/processed")
REPORT_DIR = Path("reports")

FOOD_CODE_PATTERN = re.compile(r"^[A-Z]\d{3}$")

# Coordinate boundaries calibrated using PDF page 51.
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

OUTPUT_COLUMNS = [
    "food_code",
    "food_name",
    "regions_count",
    "source_pdf_page",
    *NUTRIENT_COLUMNS,
]

REVIEW_COLUMNS = [
    "food_code",
    "source_pdf_page",
    "reason",
    "observed_value_count",
    "raw_row_text",
]

# Source-verified rows on PDF page 56 with blank fibre cells.
KNOWN_BLANK_FIBRE_ROWS = {
    (56, "I001"),
    (56, "K001"),
    (56, "K002"),
}


def get_row_words(words, y_position, tolerance=3):
    """Return the words belonging to one food row."""
    row = [
        word
        for word in words
        if abs(word["top"] - y_position) <= tolerance
    ]
    return sorted(row, key=lambda word: word["x0"])


def extract_page(page, page_number):
    """
    Extract candidate records from one PDF page.

    Incomplete rows are reviewed unless they are among the
    source-verified rows with blank fibre cells.
    """
    words = page.extract_words()

    code_words = [
        word
        for word in words
        if FOOD_CODE_PATTERN.fullmatch(word["text"])
    ]

    records = []
    reviews = []

    for code_word in code_words:
        food_code = code_word["text"]
        row_words = get_row_words(words, code_word["top"])

        raw_row_text = " ".join(
            word["text"] for word in row_words
        )

        region_words = [
            word
            for word in row_words
            if REGION_X_MIN <= word["x0"] < REGION_X_MAX
        ]

        nutrient_words = [
            word
            for word in row_words
            if word["x0"] >= NUTRIENT_X_MIN
        ]

        nutrient_values = [
            word["text"] for word in nutrient_words
        ]

        # E033 on page 50 remains isolated for separate review.
        if page_number == 50 and food_code == "E033":
            reviews.append({
                "food_code": food_code,
                "source_pdf_page": page_number,
                "reason": (
                    "Known blank fibre cells; requires explicit "
                    "source-aligned column mapping"
                ),
                "observed_value_count": len(nutrient_values),
                "raw_row_text": raw_row_text,
            })
            continue

        if len(region_words) != 1:
            reviews.append({
                "food_code": food_code,
                "source_pdf_page": page_number,
                "reason": (
                    f"Expected one region count; "
                    f"found {len(region_words)}"
                ),
                "observed_value_count": len(nutrient_values),
                "raw_row_text": raw_row_text,
            })
            continue

        # Handle the three rows verified against the original PDF.
        if (
            (page_number, food_code) in KNOWN_BLANK_FIBRE_ROWS
            and len(nutrient_values) == 6
        ):
            # Source order:
            # moisture, protein, ash, fat, [3 blank fibre cells],
            # carbohydrate, energy.
            nutrient_values = (
                nutrient_values[:4]
                + ["", "", ""]
                + nutrient_values[4:]
            )

        # All other rows must contain exactly nine nutrient values.
        if len(nutrient_values) != len(NUTRIENT_COLUMNS):
            reviews.append({
                "food_code": food_code,
                "source_pdf_page": page_number,
                "reason": (
                    f"Expected {len(NUTRIENT_COLUMNS)} nutrient values; "
                    f"found {len(nutrient_values)}"
                ),
                "observed_value_count": len(nutrient_values),
                "raw_row_text": raw_row_text,
            })
            continue

        region_word = region_words[0]

        name_words = [
            word["text"]
            for word in row_words
            if code_word["x1"] < word["x0"] < region_word["x0"]
        ]

        record = {
            "food_code": food_code,
            "food_name": " ".join(name_words),
            "regions_count": region_word["text"],
            "source_pdf_page": page_number,
        }

        record.update(
            dict(zip(NUTRIENT_COLUMNS, nutrient_values))
        )
        records.append(record)

    return records, reviews


def write_csv(path, columns, rows):
    """Write rows to CSV, including headers when there are no rows."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Extract IFCT food tables across a PDF page range."
    )
    parser.add_argument(
        "--start-page",
        type=int,
        required=True,
        help="First PDF page to process, inclusive",
    )
    parser.add_argument(
        "--end-page",
        type=int,
        required=True,
        help="Last PDF page to process, inclusive",
    )
    args = parser.parse_args()

    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"IFCT PDF not found: {PDF_PATH}"
        )

    if args.start_page < 1:
        raise ValueError("Start page must be at least 1.")

    if args.end_page < args.start_page:
        raise ValueError("End page must be >= start page.")

    all_records = []
    all_reviews = []

    with pdfplumber.open(PDF_PATH) as pdf:
        if args.end_page > len(pdf.pages):
            raise ValueError(
                f"PDF contains {len(pdf.pages)} pages; "
                f"requested page {args.end_page}."
            )

        for page_number in range(
            args.start_page,
            args.end_page + 1,
        ):
            page = pdf.pages[page_number - 1]

            records, reviews = extract_page(
                page,
                page_number,
            )

            all_records.extend(records)
            all_reviews.extend(reviews)

            print(
                f"Page {page_number}: "
                f"{len(records)} candidate records, "
                f"{len(reviews)} rows needing review"
            )

    # Detect duplicate codes within this batch.
    candidate_df = pd.DataFrame(
        all_records,
        columns=OUTPUT_COLUMNS,
    )

    duplicate_codes = []

    if not candidate_df.empty:
        duplicate_mask = candidate_df["food_code"].duplicated(
            keep=False
        )

        duplicate_codes = sorted(
            candidate_df.loc[duplicate_mask, "food_code"]
            .astype(str)
            .unique()
            .tolist()
        )

        for code in duplicate_codes:
            duplicate_rows = candidate_df[
                candidate_df["food_code"] == code
            ]

            for _, row in duplicate_rows.iterrows():
                all_reviews.append({
                    "food_code": code,
                    "source_pdf_page": row["source_pdf_page"],
                    "reason": "Duplicate food code in batch",
                    "observed_value_count": 9,
                    "raw_row_text": row["food_name"],
                })

        candidate_df = candidate_df[
            ~candidate_df["food_code"].isin(duplicate_codes)
        ]

    candidate_path = OUTPUT_DIR / (
        f"ifct_pages{args.start_page}_{args.end_page}_candidate.csv"
    )

    review_path = REPORT_DIR / (
        f"ifct_pages{args.start_page}_{args.end_page}_review.csv"
    )

    write_csv(
        candidate_path,
        OUTPUT_COLUMNS,
        candidate_df.to_dict("records"),
    )

    write_csv(
        review_path,
        REVIEW_COLUMNS,
        all_reviews,
    )

    print("\n" + "=" * 55)
    print("AAHAR AI — BATCH EXTRACTION SUMMARY")
    print("=" * 55)
    print(f"Pages processed: {args.start_page}-{args.end_page}")
    print(f"Candidate records: {len(candidate_df)}")
    print(f"Rows needing review: {len(all_reviews)}")
    print(f"Duplicate codes isolated: {len(duplicate_codes)}")
    print(f"Candidate file: {candidate_path}")
    print(f"Review file: {review_path}")
    print("\nReminder: candidate records are not automatically")
    print("source-verified merely because they passed extraction.")


if __name__ == "__main__":
    main()
