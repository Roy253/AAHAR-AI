
from pathlib import Path
import pandas as pd

INPUT_FILE = Path("data/processed/ifct_page50_positions.csv")
OUTPUT_FILE = Path("reports/ifct_page50_position_summary.csv")


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    # Only retain words that fall within the provisional numeric columns.
    numeric_words = df[df["diagnostic_column"].notna()].copy()
    numeric_words["diagnostic_column"] = (
        numeric_words["diagnostic_column"].astype(int)
    )

    summaries = []

    for food_code, group in numeric_words.groupby("food_code"):
        columns = sorted(group["diagnostic_column"].unique().tolist())

        summaries.append({
            "food_code": food_code,
            "populated_diagnostic_columns": len(columns),
            "columns_found": ",".join(map(str, columns)),
            "columns_missing_from_1_to_9": ",".join(
                str(c) for c in range(1, 10) if c not in columns
            ),
        })

    summary = pd.DataFrame(summaries).sort_values("food_code")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_FILE, index=False)

    print(f"Foods summarized: {len(summary)}")
    print(f"Report saved: {OUTPUT_FILE}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
