
from pathlib import Path
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
TARGET_PAGE = 50


def main():
    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[TARGET_PAGE - 1]
        words = page.extract_words()

    for code in ("E033", "E034"):
        matches = [w for w in words if w["text"] == code]

        if not matches:
            print(f"\n{code}: not found")
            continue

        code_word = matches[0]
        y = code_word["top"]

        # Keep words on the same visual row.
        row_words = [
            w for w in words
            if abs(w["top"] - y) <= 3
        ]
        row_words.sort(key=lambda w: w["x0"])

        print("\n" + "=" * 75)
        print(f"{code} | vertical position = {y:.1f}")
        print("=" * 75)

        for word in row_words:
            print(
                f"x={word['x0']:7.1f} "
                f"y={word['top']:6.1f} "
                f"text={word['text']}"
            )


if __name__ == "__main__":
    main()
