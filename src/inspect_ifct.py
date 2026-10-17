
"""
AAHAR AI - IFCT PDF Inspector

Purpose:
1. Check that the IFCT PDF exists.
2. Count the PDF pages.
3. Inspect selected pages for extractable text.
4. Detect whether pages contain tables.
5. Save a readable inspection report.
"""

from pathlib import Path
import pdfplumber

# Run this script from the AAHAR project root.
PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
REPORT_PATH = Path("reports/ifct_inspection.txt")

# Sample pages throughout the document (page numbers start at 1).
PAGES_TO_CHECK = [1, 2, 5, 10, 20, 50, 100, 200, 300, 400, 500, 585]


def inspect_pdf():
    """Inspect selected pages of the IFCT PDF."""

    if not PDF_PATH.exists():
        print(f"ERROR: PDF not found at: {PDF_PATH.resolve()}")
        print("Check the filename and run this script from the AAHAR root.")
        return

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report_lines = []

    with pdfplumber.open(PDF_PATH) as pdf:
        total_pages = len(pdf.pages)

        report_lines.append("AAHAR AI - IFCT PDF INSPECTION")
        report_lines.append(f"PDF: {PDF_PATH}")
        report_lines.append(f"Total pages: {total_pages}")
        report_lines.append("=" * 70)

        for page_number in PAGES_TO_CHECK:
            if page_number > total_pages:
                continue

            page = pdf.pages[page_number - 1]
            text = page.extract_text() or ""
            tables = page.extract_tables()

            report_lines.append("")
            report_lines.append("-" * 70)
            report_lines.append(f"Page: {page_number}")
            report_lines.append(f"Extracted text characters: {len(text)}")
            report_lines.append(f"Tables detected: {len(tables)}")

            if text.strip():
                report_lines.append("Text preview:")
                report_lines.append(text[:800])
            else:
                report_lines.append("No extractable text found on this page.")

            if tables:
                first_table = tables[0]
                report_lines.append("First table preview:")
                for row in first_table[:5]:
                    report_lines.append(str(row))

    REPORT_PATH.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print(f"PDF pages inspected: {len(PAGES_TO_CHECK)}")
    print(f"Total PDF pages: {total_pages}")
    print(f"Inspection report saved to: {REPORT_PATH}")
    print("\nReport preview:\n")
    print("\n".join(report_lines[:18]))


if __name__ == "__main__":
    inspect_pdf()
