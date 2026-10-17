
from pathlib import Path
import re
import csv
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
OUTPUT_FILE = Path("data/processed/ifct_page51_raw_rows.csv")
PAGE_NUMBER = 51

FOOD_CODE_PATTERN = re.compile(r"^[A-Z]\d{3}$")


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[PAGE_NUMBER - 1]
        words = page.extract_words()

    code_words = [
        word for word in words
        if FOOD_CODE_PATTERN.fullmatch(word["text"])
    ]

    rows = []

    for code_word in code_words:
        y = code_word["top"]

        row_words = [
            word for word in words
            if abs(word["top"] - y) <= 3
        ]
        row_words.sort(key=lambda word: word["x0"])

        rows.append({
            "food_code": code_word["text"],
            "row_y": round(y, 2),
            "raw_row_text": " ".join(
                word["text"] for word in row_words
            ),
            "word_count": len(row_words),
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "food_code",
                "row_y",
                "raw_row_text",
                "word_count",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"PDF page: {PAGE_NUMBER}")
    print(f"Food-code rows found: {len(rows)}")
    print(f"Output saved: {OUTPUT_FILE}")

    for row in rows:
        print(f"\n{row['food_code']}: {row['raw_row_text']}")


if __name__ == "__main__":
    main()
