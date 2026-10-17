
from pathlib import Path
import re
import pandas as pd

INPUT_FILE = Path("data/processed/ifct_page50_structured.csv")

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

# Matches values such as 11.14±0.73 or 1340±12.
VALUE_PATTERN = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)"
    r"(?:\s*[±]\s*(\d+(?:\.\d+)?))?\s*$"
)


def parse_source_value(value):
    """Return the reported value, variability, and original text."""
    original = str(value).strip()
    match = VALUE_PATTERN.fullmatch(original)

    if not match:
        return {
            "original": original,
            "mean": None,
            "variability": None,
            "valid": False,
        }

    mean_text, variability_text = match.groups()

    return {
        "original": original,
        "mean": float(mean_text),
        "variability": (
            float(variability_text)
            if variability_text is not None
            else None
        ),
        "valid": True,
    }


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"CSV not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print("AAHAR AI - NUTRITION VALUE VALIDATION")
    print(f"Rows: {len(df)}")
    print(f"Duplicate food codes: {df['food_code'].duplicated().sum()}")

    invalid_count = 0

    for column in NUTRIENT_COLUMNS:
        parsed = df[column].map(parse_source_value)
        invalid = parsed.map(lambda item: not item["valid"])
        invalid_count += int(invalid.sum())

        if invalid.any():
            print(f"\nInvalid values in {column}:")
            print(df.loc[invalid, ["food_code", column]].to_string(index=False))

    print(f"\nInvalid nutrient strings: {invalid_count}")

    print("\nExample source-value parsing:")
    for example in ["11.14±0.73", "75.60±1.16", "1340±12", "0.35"]:
        print(f"{example} -> {parse_source_value(example)}")

    print(
        "\nNote: this validates numeric formatting only. "
        "It does not verify nutrient-column alignment."
    )


if __name__ == "__main__":
    main()
