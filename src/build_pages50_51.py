
from pathlib import Path
import pandas as pd

PAGE50_FILE = Path("data/processed/ifct_page50_checkpoint.csv")
PAGE51_FILE = Path("data/processed/ifct_page51_candidate.csv")

OUTPUT_FILE = Path("data/processed/ifct_pages50_51_candidate.csv")
REPORT_FILE = Path("reports/ifct_pages50_51_build_report.txt")

KEY_COLUMNS = ["food_code", "food_name", "source_pdf_page"]


def main():
    for path in [PAGE50_FILE, PAGE51_FILE]:
        if not path.exists():
            raise FileNotFoundError(f"Missing input: {path}")

    page50 = pd.read_csv(PAGE50_FILE, dtype=str).fillna("")
    page51 = pd.read_csv(PAGE51_FILE, dtype=str).fillna("")

    # Confirm that each file contains the expected source page.
    if not (page50["source_pdf_page"] == "50").all():
        raise ValueError("Page-50 checkpoint contains unexpected source pages.")

    if not (page51["source_pdf_page"] == "51").all():
        raise ValueError("Page-51 candidate contains unexpected source pages.")

    combined = pd.concat([page50, page51], ignore_index=True, sort=False)

    duplicates = combined.loc[
        combined["food_code"].duplicated(keep=False)
    ].sort_values("food_code")

    if not duplicates.empty:
        raise ValueError(
            "Duplicate food codes found across pages:\n"
            + duplicates[KEY_COLUMNS].to_string(index=False)
        )

    combined = combined.sort_values("food_code").reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    summary = [
        "AAHAR AI - PAGES 50-51 BUILD REPORT",
        f"Page 50 input rows: {len(page50)}",
        f"Page 51 input rows: {len(page51)}",
        f"Combined rows: {len(combined)}",
        f"Unique food codes: {combined['food_code'].nunique()}",
        "Duplicate food codes: 0",
        "",
        "IMPORTANT:",
        "This is a combined candidate dataset, not a fully source-verified dataset.",
        "Page-50 and page-51 records retain their original source-page references.",
        "Format checks do not independently verify all nutrient values.",
        f"Output: {OUTPUT_FILE}",
    ]

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(summary), encoding="utf-8")

    print("\n".join(summary))


if __name__ == "__main__":
    main()
