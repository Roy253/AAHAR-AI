
from pathlib import Path
import re

import pandas as pd
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
CSV_PATH = Path("data/processed/ifct_pages52_55_candidate.csv")
REPORT_PATH = Path("reports/ifct_pages52_55_validation.csv")

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

REQUIRED_COLUMNS = [
    "food_code",
    "food_name",
    "regions_count",
    "source_pdf_page",
    *NUTRIENT_COLUMNS,
]

VALUE_PATTERN = re.compile(
    r"^\d+(?:\.\d+)?(?:±\d+(?:\.\d+)?)?$"
)


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(PDF_PATH)

    if not CSV_PATH.exists():
        raise FileNotFoundError(CSV_PATH)

    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")

    missing_columns = [
        col for col in REQUIRED_COLUMNS if col not in df.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing CSV columns: {missing_columns}")

    results = []

    with pdfplumber.open(PDF_PATH) as pdf:
        for _, row in df.iterrows():
            code = row["food_code"]
            issues = []

            if not code:
                issues.append("Missing food code")

            if not row["food_name"].strip():
                issues.append("Missing food name")

            try:
                page_number = int(row["source_pdf_page"])
                if page_number < 1 or page_number > len(pdf.pages):
                    raise ValueError
            except (ValueError, TypeError):
                issues.append("Invalid source page")
                page_number = None

            if not row["regions_count"].isdigit():
                issues.append("Invalid region count")

            for col in NUTRIENT_COLUMNS:
                value = row[col].strip()

                if not value:
                    issues.append(f"Blank nutrient: {col}")
                elif not VALUE_PATTERN.fullmatch(value):
                    issues.append(f"Invalid nutrient format: {col}")

            source_row_found = False

            if page_number is not None and code:
                page_text = (
                    pdf.pages[page_number - 1].extract_text() or ""
                )

                matching_lines = [
                    line for line in page_text.splitlines()
                    if code in line
                ]

                source_row_found = bool(matching_lines)

                if not source_row_found:
                    issues.append("Food code not found in source text")
                else:
                    source_text = " ".join(matching_lines)

                    # Verify values occur in the source row text.
                    # This does NOT prove column alignment.
                    for col in NUTRIENT_COLUMNS:
                        value = row[col].strip()
                        if value and value not in source_text:
                            issues.append(
                                f"Value absent from source row: {col}"
                            )

            results.append({
                "food_code": code,
                "food_name": row["food_name"],
                "source_pdf_page": row["source_pdf_page"],
                "source_row_found": source_row_found,
                "status": "PASS" if not issues else "REVIEW",
                "issues": "; ".join(issues),
            })

    report = pd.DataFrame(results)
    duplicate_mask = df["food_code"].duplicated(keep=False)

    if duplicate_mask.any():
        duplicate_codes = set(df.loc[duplicate_mask, "food_code"])
        report.loc[
            report["food_code"].isin(duplicate_codes), "status"
        ] = "REVIEW"

        report.loc[
            report["food_code"].isin(duplicate_codes), "issues"
        ] += "; Duplicate food code"

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(REPORT_PATH, index=False, encoding="utf-8-sig")

    print("AAHAR AI — BATCH VALIDATION")
    print(f"Records checked: {len(report)}")
    print(f"Format/source-text passes: {(report.status == 'PASS').sum()}")
    print(f"Needs review: {(report.status == 'REVIEW').sum()}")
    print(f"Duplicate codes in source CSV: {int(duplicate_mask.sum())}")
    print(f"Report saved: {REPORT_PATH}")

    print("\nRows needing review:")
    flagged = report[report["status"] == "REVIEW"]
    print(
        flagged[["food_code", "source_pdf_page", "issues"]]
        .to_string(index=False)
        if not flagged.empty
        else "None"
    )

    print(
        "\nImportant: PASS means format and source-text checks passed. "
        "It does not certify nutrient-column alignment."
    )


if __name__ == "__main__":
    main()
