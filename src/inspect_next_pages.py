
from pathlib import Path
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
OUTPUT_FILE = Path("reports/ifct_page_inspection.txt")

# Inspect a small range after page 50.
START_PAGE = 51
END_PAGE = 60


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    lines = []

    with pdfplumber.open(PDF_PATH) as pdf:
        end_page = min(END_PAGE, len(pdf.pages))

        for page_number in range(START_PAGE, end_page + 1):
            page = pdf.pages[page_number - 1]
            text = page.extract_text() or ""

            lines.append(f"\n{'=' * 60}")
            lines.append(f"PDF PAGE {page_number}")
            lines.append(f"{'=' * 60}")
            lines.append(text[:1800] if text else "[No extractable text]")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print(f"Pages inspected: {START_PAGE}-{end_page}")
    print(f"Report saved to: {OUTPUT_FILE}")
    print("\n".join(lines[:35]))


if __name__ == "__main__":
    main()
