
from pathlib import Path
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
PAGE_NUMBER = 51


def main():
    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[PAGE_NUMBER - 1]
        words = page.extract_words()

    code = next(
        (w for w in words if w["text"] == "E038"),
        None,
    )

    if code is None:
        raise ValueError("E038 was not found on PDF page 51.")

    y = code["top"]

    row = sorted(
        [w for w in words if abs(w["top"] - y) <= 3],
        key=lambda w: w["x0"],
    )

    print(f"E038 row vertical position: {y:.2f}")
    print("=" * 70)

    for word in row:
        print(
            f"x={word['x0']:7.2f} "
            f"x1={word['x1']:7.2f} "
            f"text={word['text']}"
        )


if __name__ == "__main__":
    main()
