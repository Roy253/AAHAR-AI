
from pathlib import Path
import pandas as pd

PROCESSED_DIR = Path("data/processed")
STRUCTURED_FILE = PROCESSED_DIR / "ifct_page50_structured.csv"
REVIEW_FILE = PROCESSED_DIR / "ifct_page50_review.csv"

REPORT_DIR = Path("reports")
SUMMARY_FILE = REPORT_DIR / "dataset_build_summary.txt"
AUDIT_FILE = REPORT_DIR / "dataset_build_audit.csv"


def main():
    if not STRUCTURED_FILE.exists():
        raise FileNotFoundError(f"Missing file: {STRUCTURED_FILE}")

    if not REVIEW_FILE.exists():
        raise FileNotFoundError(f"Missing file: {REVIEW_FILE}")

    structured = pd.read_csv(STRUCTURED_FILE, dtype=str)
    review = pd.read_csv(REVIEW_FILE, dtype=str)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    structured_codes = set(structured["food_code"].dropna())
    review_codes = set(review["food_code"].dropna())

    audit_rows = []

    for _, row in structured.iterrows():
        audit_rows.append({
            "food_code": row["food_code"],
            "food_name": row["food_name"],
            "status": "parsed_pending_source_validation",
            "reason": "Record has expected field count; verify against source",
        })

    for _, row in review.iterrows():
        audit_rows.append({
            "food_code": row["food_code"],
            "food_name": row["food_name"],
            "status": "needs_review",
            "reason": row["review_reason"],
        })

    audit = pd.DataFrame(audit_rows).sort_values("food_code")
    audit.to_csv(AUDIT_FILE, index=False)

    summary = [
        "AAHAR AI - DATASET BUILD SUMMARY",
        "=" * 50,
        f"Structured records: {len(structured)}",
        f"Records needing review: {len(review)}",
        f"Unique structured codes: {len(structured_codes)}",
        f"Unique review codes: {len(review_codes)}",
        f"Codes appearing in both: {len(structured_codes & review_codes)}",
        f"Total unique codes: {len(structured_codes | review_codes)}",
        "",
        "Important:",
        "- Parsed does not mean fully source-verified.",
        "- Review records are not model-ready.",
        "- Missing values must not be replaced with zero without evidence.",
        "",
        f"Audit CSV: {AUDIT_FILE}",
    ]

    SUMMARY_FILE.write_text("\n".join(summary), encoding="utf-8")

    print("\n".join(summary))


if __name__ == "__main__":
    main()
