
from pathlib import Path
import pandas as pd

PAGE_50_51 = Path("data/processed/ifct_pages50_51_reviewed.csv")
PAGE_52_55 = Path("data/processed/ifct_pages52_55_reviewed.csv")

OUTPUT = Path("data/processed/ifct_pages50_55_consolidated.csv")
AUDIT = Path("reports/ifct_pages50_55_consolidation_audit.csv")

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


def main():
    for path in [PAGE_50_51, PAGE_52_55]:
        if not path.exists():
            raise FileNotFoundError(
                f"Required reviewed dataset not found: {path}"
            )

    first = pd.read_csv(PAGE_50_51, dtype=str).fillna("")
    second = pd.read_csv(PAGE_52_55, dtype=str).fillna("")

    for name, df in [
        ("pages 50–51", first),
        ("pages 52–55", second),
    ]:
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"{name} is missing columns: {missing}")

        if df["food_code"].eq("").any():
            raise ValueError(f"{name} contains blank food codes")

    combined = pd.concat([first, second], ignore_index=True)

    duplicate_mask = combined["food_code"].duplicated(keep=False)
    duplicate_rows = combined.loc[duplicate_mask].sort_values("food_code")

    if not duplicate_rows.empty:
        print("Duplicate food codes found across batches:")
        print(
            duplicate_rows[
                ["food_code", "food_name", "source_pdf_page"]
            ].to_string(index=False)
        )
        raise ValueError(
            "Consolidation stopped. Investigate duplicate codes first."
        )

    if combined["food_name"].eq("").any():
        missing_names = combined.loc[
            combined["food_name"].eq(""),
            ["food_code", "source_pdf_page"],
        ]
        print(missing_names.to_string(index=False))
        raise ValueError("Consolidation stopped: missing food names.")

    combined["source_pdf_page"] = pd.to_numeric(
        combined["source_pdf_page"], errors="raise"
    ).astype(int)

    combined = combined.sort_values(
        ["source_pdf_page", "food_code"]
    ).reset_index(drop=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    audit = pd.DataFrame([{
        "pages_50_51_rows": len(first),
        "pages_52_55_rows": len(second),
        "combined_rows": len(combined),
        "unique_food_codes": combined["food_code"].nunique(),
        "duplicate_food_codes": int(
            combined["food_code"].duplicated().sum()
        ),
        "blank_food_names": int(
            combined["food_name"].eq("").sum()
        ),
        "source_pages": ",".join(
            map(str, sorted(combined["source_pdf_page"].unique()))
        ),
        "output_file": str(OUTPUT),
    }])

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(AUDIT, index=False, encoding="utf-8-sig")

    print("\nAAHAR AI — CONSOLIDATION SUMMARY")
    print(f"Pages 50–51 records: {len(first)}")
    print(f"Pages 52–55 records: {len(second)}")
    print(f"Combined records: {len(combined)}")
    print(f"Unique food codes: {combined['food_code'].nunique()}")
    print(f"Source pages: {sorted(combined['source_pdf_page'].unique())}")
    print(f"Dataset saved: {OUTPUT}")
    print(f"Audit saved: {AUDIT}")
    print(
        "\nReminder: structural checks do not guarantee that "
        "every nutrient value has been source-verified."
    )


if __name__ == "__main__":
    main()
