
from pathlib import Path
import pandas as pd

INPUT_FILE = Path("data/processed/ifct_page51_raw_rows.csv")
OUTPUT_FILE = Path("reports/ifct_page51_value_review.csv")


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    df = pd.read_csv(INPUT_FILE, dtype=str)

    # Keep the original extracted row intact for manual source comparison.
    review = df[["food_code", "row_y", "raw_row_text"]].copy()
    review["source_checked"] = "NO"
    review["review_notes"] = ""

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    review.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"Rows prepared for source review: {len(review)}")
    print(f"Review file: {OUTPUT_FILE}")
    print("\nFirst five rows:")
    print(review.head().to_string(index=False))


if __name__ == "__main__":
    main()
