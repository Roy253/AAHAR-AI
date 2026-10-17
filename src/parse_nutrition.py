
from pathlib import Path
import csv
import re
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
OUTPUT_FILE = Path("data/processed/ifct_page50_structured.csv")
TARGET_PAGE = 50

FOOD_CODE_PATTERN = re.compile(r"^([A-Z]\d{3})\s+")

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
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[TARGET_PAGE - 1]
        words = page.extract_words()

    # Group words by their vertical row positions.
    code_words = [
        word for word in words
        if FOOD_CODE_PATTERN.fullmatch(word["text"] + " ")
    ]

    records = []

    for code_word in code_words:
        row_y = code_word["top"]
        row_words = [
            word for word in words
            if abs(word["top"] - row_y) <= 3
        ]
        row_words.sort(key=lambda word: word["x0"])

        # Numeric values are located to the right of the food description.
        numeric_words = [
            word for word in row_words
            if word["x0"] >= 300
        ]

        # The region count is the first numeric item.
        if not numeric_words:
            continue

        regions_count = numeric_words[0]["text"]
        nutrient_values = [word["text"] for word in numeric_words[1:]]

        # Preserve the observed order, but only accept rows with either
        # nine values or six values (the known E033 source layout).
        if len(nutrient_values) == 9:
            mapped_values = nutrient_values
        elif code_word["text"] == "E033" and len(nutrient_values) == 6:
            mapped_values = [
                *nutrient_values[:4],
                "", "", "",
                *nutrient_values[4:],
            ]
        else:
            print(
                f"Needs review: {code_word['text']} "
                f"has {len(nutrient_values)} nutrient values"
            )
            continue

        record = {
            "food_code": code_word["text"],
            "regions_count": regions_count,
            "source_pdf_page": TARGET_PAGE,
        }

        # The food name is captured from the original parsed report
        # in the next pipeline stage; don't infer it from numeric values.
        for column, value in zip(NUTRIENT_COLUMNS, mapped_values):
            record[column] = value

        records.append(record)

    fields = [
        "food_code",
        "regions_count",
        "source_pdf_page",
        *NUTRIENT_COLUMNS,
    ]

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    print(f"Records exported: {len(records)}")
    print(f"Output: {OUTPUT_FILE}")
    print("Blank nutrient fields are preserved as empty cells.")


if __name__ == "__main__":
    main()
