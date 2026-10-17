
from pathlib import Path
import pandas as pd

SOURCE = Path("data/processed/ifct_pages52_55_candidate.csv")
DESTINATION = Path("data/processed/ifct_pages52_55_reviewed.csv")
AUDIT = Path("reports/e065_correction_audit.csv")

FOOD_CODE = "E065"
VERIFIED_NAME = (
    "Water melon, dark green (sugar baby) "
    "(Citrullus vulgaris)"
)


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    df = pd.read_csv(SOURCE, dtype=str).fillna("")

    matches = df.index[df["food_code"] == FOOD_CODE].tolist()

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one {FOOD_CODE} record; found {len(matches)}"
        )

    idx = matches[0]
    old_name = df.at[idx, "food_name"]

    if old_name and old_name != VERIFIED_NAME:
        raise ValueError(
            f"Existing name is not blank: {old_name!r}. "
            "Review manually; no correction applied."
        )

    df.at[idx, "food_name"] = VERIFIED_NAME

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DESTINATION, index=False, encoding="utf-8-sig")

    audit = pd.DataFrame([{
        "food_code": FOOD_CODE,
        "old_name": old_name,
        "new_name": VERIFIED_NAME,
        "source_pdf_page": "52",
        "correction_basis": "Original IFCT PDF row inspected",
    }])

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(AUDIT, index=False, encoding="utf-8-sig")

    print("E065 correction saved.")
    print(f"Reviewed dataset: {DESTINATION}")
    print(f"Audit report: {AUDIT}")
    print(f"Total records: {len(df)}")
    print(f"Unique food codes: {df['food_code'].nunique()}")
    print("All nutrient values preserved.")


if __name__ == "__main__":
    main()
