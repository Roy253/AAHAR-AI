
from pathlib import Path
import re
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
OUTPUT_FILE = Path("reports/ifct_page51_rows.txt")
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

    lines = [
        "AAHAR AI - PAGE 51 ROW INSPECTION",
        f"PDF page: {PAGE_NUMBER}",
        f"Food codes found: {len(code_words)}",
        "",
    ]

    for code_word in code_words:
        y = code_word["top"]

        row_words = [
            word for word in words
            if abs(word["top"] - y) <= 3
        ]
        row_words.sort(key=lambda word: word["x0"])

        lines.append(
            f"{code_word['text']} | "
            + " ".join(word["text"] for word in row_words)
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print(f"Food codes found: {len(code_words)}")
    print(f"Report saved: {OUTPUT_FILE}")
    print("\n".join(lines[:18]))


if __name__ == "__main__":
    main()
