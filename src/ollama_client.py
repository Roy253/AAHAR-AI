
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def ask_ollama(prompt: str, timeout: int = 180) -> str:
    """
    Generate a response using the local Ollama model.
    No paid LLM API is required.
    """
    if not prompt or not prompt.strip():
        return "Please enter a question."

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt.strip(),
                "stream": False,
            },
            timeout=timeout,
        )
        response.raise_for_status()

        result = response.json()
        answer = result.get("response", "").strip()

        return answer or "The local model returned an empty response."

    except requests.exceptions.Timeout:
        return "The local AI took too long to respond. Please try again."

    except requests.exceptions.ConnectionError:
        return (
            "Cannot connect to Ollama. Make sure Ollama is running "
            "on your computer."
        )

    except requests.exceptions.RequestException as error:
        return f"Local AI request failed: {error}"
