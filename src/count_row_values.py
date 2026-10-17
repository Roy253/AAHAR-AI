
from pathlib import Path
import re
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
OUTPUT_FILE = Path("reports/ifct_page50_row_counts.txt")
TARGET_PAGE = 50

FOOD_CODE_PATTERN = re.compile(r"^[A-Z]\d{3}$")
EXPECTED_VALUES = 9


def main():
    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[TARGET_PAGE - 1]
        words = page.extract_words()

    code_words = [
        word for word in words
        if FOOD_CODE_PATTERN.fullmatch(word["text"])
    ]

    results = []

    for code_word in code_words:
        y = code_word["top"]

        row_words = [
            word for word in words
            if abs(word["top"] - y) <= 3
        ]
        row_words.sort(key=lambda word: word["x0"])

        value_words = [
            word for word in row_words
            if word["x0"] > 300
        ]

        count = len(value_words)
        status = "CHECK" if count != EXPECTED_VALUES else "REVIEW"

        results.append(
            f"{code_word['text']} | count={count} | {status} | "
            + " ".join(word["text"] for word in value_words)
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(results), encoding="utf-8")

    flagged = [
        row for row in results
        if " | CHECK | " in row
    ]

    print(f"Food records inspected: {len(results)}")
    print(f"Rows with counts other than {EXPECTED_VALUES}: {len(flagged)}")
    print(f"Report saved to: {OUTPUT_FILE}")
    print("\nRows needing investigation:")

    for row in flagged:
        print(row)


if __name__ == "__main__":
    main()
