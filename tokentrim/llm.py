"""Talks to Ollama on this PC. Any failure becomes an LLMError, so callers can skip the AI step."""
import httpx

from .config import load_config


class LLMError(Exception):
    pass


def is_available():
    """True if Ollama answers and the configured model is downloaded."""
    settings = load_config()["ollama"]
    try:
        response = httpx.get(
            settings["url"] + "/api/tags",
            timeout=3,
        )
        response.raise_for_status()
        names = [
            model.get("name", "")
            for model in response.json().get("models", [])
        ]
    except (httpx.HTTPError, ValueError):
        return False

    return settings["model"] in names


def chat(prompt, system=None):
    """Send one prompt and return the model's answer as text."""
    settings = load_config()["ollama"]

    messages = []
    if system:
        messages.append({
            "role": "system",
            "content": system,
        })

    messages.append({
        "role": "user",
        "content": prompt,
    })

    payload = {
        "model": settings["model"],
        "messages": messages,
        "stream": False,
        "keep_alive": "5m",
        "options": {
            "temperature": 0.2,
            "num_ctx": settings["num_ctx"],
        },
    }

    try:
        response = httpx.post(
            settings["url"] + "/api/chat",
            json=payload,
            timeout=settings["timeout_seconds"],
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, ValueError) as error:
        raise LLMError(f"Ollama call failed: {error}") from error