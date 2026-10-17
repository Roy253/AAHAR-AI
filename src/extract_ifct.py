
from pathlib import Path
import re
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
OUTPUT_PATH = Path("data/raw/ifct_page50_parsed.txt")
TARGET_PAGE = 50

# Match food codes such as E017, E018, A020, and B001.
FOOD_CODE_PATTERN = re.compile(r"^[A-Z]\d{3}\b")


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH.resolve()}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[TARGET_PAGE - 1]
        text = page.extract_text() or ""

    lines = text.splitlines()

    matched_lines = [
        line.strip()
        for line in lines
        if FOOD_CODE_PATTERN.match(line.strip())
    ]

    report = [
        "AAHAR AI - IFCT TEXT PARSING EXPERIMENT",
        f"PDF page: {TARGET_PAGE}",
        f"Extracted lines: {len(lines)}",
        f"Potential food records: {len(matched_lines)}",
        "",
        "POTENTIAL FOOD RECORDS",
        "=" * 70,
        *matched_lines,
    ]

    if not matched_lines:
        report.extend([
            "",
            "No food records matched the pattern.",
            "",
            "FULL EXTRACTED TEXT",
            "=" * 70,
            text,
        ])

    OUTPUT_PATH.write_text("\n".join(report), encoding="utf-8")

    print(f"Extracted lines: {len(lines)}")
    print(f"Potential food records: {len(matched_lines)}")
    print(f"Report saved to: {OUTPUT_PATH}")
    print("\n".join(report[:20]))


if __name__ == "__main__":
    main()
