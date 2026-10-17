
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def ask_aahar_ai(question):
    """Send a question to the local Ollama model."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": (
                    "You are AAHAR AI, a helpful hostel nutrition assistant. "
                    "Give practical, affordable food suggestions. "
                    "Do not invent exact nutrition values or food prices. "
                    "If precise data is unavailable, say so.\n\n"
                    f"User question: {question}"
                ),
                "stream": False,
            },
            timeout=300,
        )

        response.raise_for_status()
        return response.json()["response"]

    except requests.exceptions.Timeout:
        return "The local AI took too long to respond. Please try again."

    except requests.exceptions.RequestException as error:
        return f"Could not connect to Ollama: {error}"


if __name__ == "__main__":
    question = (
        "I am a vegetarian hostel student. "
        "Suggest three affordable protein-rich snacks in India."
    )

    print("\nAAHAR AI — Local LLM Test\n")
    print(ask_aahar_ai(question))
