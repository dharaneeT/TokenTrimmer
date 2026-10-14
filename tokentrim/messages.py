"""Chat message helpers. A message is a dict like {"role": "user", "content": "text"}."""
import json
from pathlib import Path

from .tokens import count_tokens

ROLES = ("system", "user", "assistant", "tool")


def content_text(message):
    """Return the text of a message, or "" if it has no text."""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text", "")))
        return "\n".join(parts)
    return ""


def message_tokens(message):
    return count_tokens(content_text(message))


def total_tokens(messages):
    return sum(message_tokens(m) for m in messages)


def has_special_content(message):
    """True for tool calls, tool replies and non-text content such as images."""
    if message.get("role") == "tool" or message.get("tool_calls"):
        return True
    return not isinstance(message.get("content"), str)


def protected_indexes(messages):
    """Positions of messages no step may change: system, special, and the newest."""
    protected = set()
    for index, message in enumerate(messages):
        if message.get("role") == "system" or has_special_content(message):
            protected.add(index)
    if messages:
        protected.add(len(messages) - 1)
    return protected


def load_messages(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON: {error}")
    if isinstance(data, dict) and "messages" in data:
        data = data["messages"]
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a list of messages")
    for number, message in enumerate(data, 1):
        if not isinstance(message, dict) or message.get("role") not in ROLES:
            raise ValueError(f"Message {number} needs a 'role' of: {', '.join(ROLES)}")
    return data


def save_messages(path, messages):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(messages, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def parse_text_chat(text):
    """Turn a text file with '### system', '### user', '### assistant' headers into messages."""
    messages = []
    role = None
    lines = []

    def flush():
        if role is not None:
            messages.append({"role": role, "content": "\n".join(lines).strip("\n")})

    for line in text.splitlines():
        header = line.strip()
        if header.startswith("### ") and header[4:].strip().lower() in ROLES:
            flush()
            role = header[4:].strip().lower()
            lines = []
        else:
            lines.append(line)
    flush()
    if not messages:
        raise ValueError("No '### user' or '### assistant' header lines found in the text")
    return messages