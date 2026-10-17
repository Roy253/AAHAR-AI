
from pathlib import Path
import pdfplumber

PDF_PATH = Path("data/source_docs/IFCT2017_16122024.pdf")
TARGET_PAGE = 50


def print_words(words, label):
    print(f"\n{'=' * 75}\n{label}\n{'=' * 75}")

    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        print(
            f"y={word['top']:7.1f} "
            f"x={word['x0']:7.1f} "
            f"{word['text']}"
        )


def main():
    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[TARGET_PAGE - 1]
        words = page.extract_words()

    # Inspect the column-header area. The ranges are approximate
    # and based on the coordinates seen in the previous output.
    header_words = [
        w for w in words
        if 300 <= w["top"] <= 410
    ]

    print_words(header_words, "HEADER WORD POSITIONS")

    for code in ("E033", "E034"):
        code_word = next(
            (w for w in words if w["text"] == code),
            None
        )

        if code_word is None:
            print(f"\n{code} not found.")
            continue

        row_words = [
            w for w in words
            if abs(w["top"] - code_word["top"]) <= 3
        ]

        print_words(row_words, f"{code} ROW")


if __name__ == "__main__":
    main()
