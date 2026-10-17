
from pathlib import Path
import re
import pandas as pd

INPUT_FILE = Path("data/processed/ifct_page51_raw_rows.csv")
OUTPUT_FILE = Path("reports/ifct_page51_validation.csv")

# IFCT food codes such as E038.
FOOD_CODE_PATTERN = re.compile(r"\b([A-Z]\d{3})\b")

# Numeric values, including the source's ± uncertainty notation.
VALUE_PATTERN = re.compile(
    r"(?<![\w.])\d+(?:\.\d+)?(?:±\d+(?:\.\d+)?)?"
)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    df = pd.read_csv(INPUT_FILE, dtype=str)
    results = []

    for _, row in df.iterrows():
        raw = str(row["raw_row_text"])
        code = str(row["food_code"])

        # Remove the code and count numeric tokens in the remaining row.
        text = raw.replace(code, "", 1)
        values = VALUE_PATTERN.findall(text)

        # The first numeric token is the region count.
        nutrient_values = values[1:] if values else []

        results.append({
            "food_code": code,
            "numeric_tokens_including_region": len(values),
            "nutrient_values_detected": len(nutrient_values),
            "status": (
                "COUNT_CHECK"
                if len(nutrient_values) != 9
                else "SOURCE_ALIGNMENT_REQUIRED"
            ),
        })

    report = pd.DataFrame(results)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(OUTPUT_FILE, index=False)

    print(f"Rows checked: {len(report)}")
    print(f"Report saved: {OUTPUT_FILE}")
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
