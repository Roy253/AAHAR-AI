
from pathlib import Path
import re
import pandas as pd

INPUT_FILE = Path("data/processed/ifct_page51_candidate.csv")
REPORT_FILE = Path("reports/ifct_page51_quality_report.csv")

REQUIRED_COLUMNS = [
    "food_code",
    "food_name",
    "regions_count",
    "source_pdf_page",
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

VALUE_PATTERN = re.compile(
    r"^\s*\d+(?:\.\d+)?(?:±\d+(?:\.\d+)?)?\s*$"
)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    df = pd.read_csv(INPUT_FILE, dtype=str).fillna("")

    missing_columns = [
        col for col in REQUIRED_COLUMNS if col not in df.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    results = []

    for _, row in df.iterrows():
        problems = []

        if not row["food_name"].strip():
            problems.append("Missing food name")

        if row["source_pdf_page"] != "51":
            problems.append("Unexpected source page")

        if not row["regions_count"].isdigit():
            problems.append("Invalid region count")

        for col in REQUIRED_COLUMNS[4:]:
            if not VALUE_PATTERN.fullmatch(row[col]):
                problems.append(f"Review nutrient: {col}")

        results.append({
            "food_code": row["food_code"],
            "food_name": row["food_name"],
            "status": "PASS" if not problems else "REVIEW",
            "issues": "; ".join(problems),
        })

    report = pd.DataFrame(results)
    duplicates = df["food_code"].duplicated().sum()

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(REPORT_FILE, index=False, encoding="utf-8-sig")

    print("AAHAR AI — PAGE 51 QUALITY CHECK")
    print(f"Rows: {len(df)}")
    print(f"Duplicate food codes: {duplicates}")
    print(f"Passed format checks: {(report['status'] == 'PASS').sum()}")
    print(f"Needs review: {(report['status'] == 'REVIEW').sum()}")
    print(f"Report saved: {REPORT_FILE}")

    print("\nRows needing review:")
    print(
        report.loc[report["status"] == "REVIEW"].to_string(index=False)
        if (report["status"] == "REVIEW").any()
        else "None"
    )


if __name__ == "__main__":
    main()
