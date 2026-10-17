
from pathlib import Path
import csv
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
OUTPUT_FILE = Path("data/processed/ifct_page50_positions.csv")
TARGET_PAGE = 50

# Approximate x-coordinates observed in the PDF.
# These are diagnostic boundaries, not yet verified nutrient mappings.
COLUMN_BOUNDARIES = [
    300, 350, 410, 465, 520, 575, 630, 690, 750, 820
]


def get_column(x):
    for i in range(len(COLUMN_BOUNDARIES) - 1):
        if COLUMN_BOUNDARIES[i] <= x < COLUMN_BOUNDARIES[i + 1]:
            return i + 1
    return None


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[TARGET_PAGE - 1]
        words = page.extract_words()

    food_codes = [
        word for word in words
        if len(word["text"]) == 4
        and word["text"][0].isalpha()
        and word["text"][1:].isdigit()
    ]

    records = []

    for code_word in food_codes:
        row_y = code_word["top"]

        row_words = [
            word for word in words
            if abs(word["top"] - row_y) <= 3
        ]

        row_words.sort(key=lambda word: word["x0"])

        for word in row_words:
            records.append({
                "food_code": code_word["text"],
                "row_y": round(row_y, 2),
                "word": word["text"],
                "x_position": round(word["x0"], 2),
                "diagnostic_column": get_column(word["x0"]),
            })

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "food_code",
                "row_y",
                "word",
                "x_position",
                "diagnostic_column",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"Food-code rows found: {len(food_codes)}")
    print(f"Positional entries saved: {len(records)}")
    print(f"Output: {OUTPUT_FILE}")
    print("Column boundaries are provisional; verify before mapping nutrients.")


if __name__ == "__main__":
    main()
