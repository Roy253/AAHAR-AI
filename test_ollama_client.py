
from src.ollama_client import ask_ollama


def main():
    print("\n" + "=" * 45)
    print("       AAHAR AI - LOCAL LLM TEST")
    print("=" * 45)

    question = (
        "I am a vegetarian hostel student in India with a limited budget. "
        "Suggest three affordable protein-rich foods. "
        "Explain briefly how I can include them in my daily meals. "
        "Do not invent exact nutrition values or prices."
    )

    print("\nQuestion:")
    print(question)
    print("\nGenerating response using local Ollama model...")
    print("Please wait; the first response may take some time.\n")

    answer = ask_ollama(question)

    print("-" * 45)
    print("AAHAR AI RESPONSE")
    print("-" * 45)
    print(answer)
    print("-" * 45)
    print("Test completed.")


if __name__ == "__main__":
    main()
