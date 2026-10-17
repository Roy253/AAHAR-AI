
from pathlib import Path
import csv
import re

INPUT_FILE = Path("data/raw/ifct_page50_parsed.txt")
OUTPUT_FILE = Path("data/processed/ifct_page50_recovered.csv")

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

RECORD_PATTERN = re.compile(r"^([A-Z]\d{3})\s+(.+?)\s+(\d+)\s+(.+)$")


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    records = []
    review = []

    for line in INPUT_FILE.read_text(encoding="utf-8").splitlines():
        match = RECORD_PATTERN.match(line.strip())
        if not match:
            continue

        code, name, regions, values_text = match.groups()
        values = values_text.split()

        # E033 has three blank fibre fields in the original table.
        if code == "E033" and len(values) == 6:
            values = values[:4] + ["", "", ""] + values[4:]

        if len(values) != 9:
            review.append((code, len(values)))
            continue

        record = {
            "food_code": code,
            "food_name": name,
            "regions_count": regions,
            "source_pdf_page": 50,
        }
        record.update(dict(zip(NUTRIENT_COLUMNS, values)))
        records.append(record)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "food_code", "food_name", "regions_count", "source_pdf_page",
        *NUTRIENT_COLUMNS,
    ]

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    print(f"Recovered records: {len(records)}")
    print(f"Records needing review: {review}")
    print(f"Recovered file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
