
from pathlib import Path
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
OUTPUT_FILE = Path("reports/ifct_page50_headers.txt")
TARGET_PAGE = 50


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[TARGET_PAGE - 1]
        words = page.extract_words()

    # Save words and coordinates from the upper portion of page 50.
    header_words = [
        word for word in words
        if word["top"] < 400
    ]

    header_words.sort(key=lambda word: (word["top"], word["x0"]))

    lines = [
        "AAHAR AI - IFCT HEADER INSPECTION",
        f"PDF page: {TARGET_PAGE}",
        "",
        "Words and positions:",
    ]

    for word in header_words:
        lines.append(
            f"y={word['top']:7.1f} "
            f"x={word['x0']:7.1f} "
            f"text={word['text']}"
        )

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print(f"Header inspection saved to: {OUTPUT_FILE}")
    print("\n".join(lines[:45]))


if __name__ == "__main__":
    main()
