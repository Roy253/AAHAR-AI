
from pathlib import Path
import re
import pandas as pd

SOURCE_FILE = Path("data/raw/ifct_page50_parsed.txt")
STRUCTURED_FILE = Path("data/processed/ifct_page50_structured.csv")
AUDIT_FILE = Path("reports/ifct_page50_audit.txt")

FOOD_CODE_PATTERN = re.compile(r"^([A-Z]\d{3})\s+")


def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(SOURCE_FILE)

    if not STRUCTURED_FILE.exists():
        raise FileNotFoundError(STRUCTURED_FILE)

    source_lines = SOURCE_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    source_codes = []
    for line in source_lines:
        match = FOOD_CODE_PATTERN.match(line.strip())
        if match:
            source_codes.append(match.group(1))

    df = pd.read_csv(STRUCTURED_FILE, dtype=str)
    structured_codes = df["food_code"].tolist()

    missing_from_csv = [
        code for code in source_codes
        if code not in structured_codes
    ]

    unexpected_in_csv = [
        code for code in structured_codes
        if code not in source_codes
    ]

    report = [
        "AAHAR AI - EXTRACTION AUDIT",
        f"Source food records: {len(source_codes)}",
        f"Structured CSV records: {len(structured_codes)}",
        f"Unique source codes: {len(set(source_codes))}",
        f"Unique CSV codes: {df['food_code'].nunique()}",
        "",
        f"Missing from CSV: {missing_from_csv}",
        f"Unexpected in CSV: {unexpected_in_csv}",
        "",
        "Source codes:",
        ", ".join(source_codes),
    ]

    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_FILE.write_text("\n".join(report), encoding="utf-8")

    print("\n".join(report))
    print(f"\nAudit saved to: {AUDIT_FILE}")


if __name__ == "__main__":
    main()
