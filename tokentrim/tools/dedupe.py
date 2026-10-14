"""Step 2: replace a later identical code block (80 tokens or more) with a short reference.

The first copy always stays, so the start of a prompt never changes as a chat grows.
"""
import copy
import re

from ..messages import protected_indexes
from ..tokens import count_tokens

NAME = "dedupe_code_blocks"
KIND = "same meaning"
MIN_TOKENS = 80

_FENCE = re.compile(r"^(```[^\n]*)\n(.*?)\n?^```[ \t\r]*$", re.MULTILINE | re.DOTALL)


def apply(messages, budget=None):
    result = copy.deepcopy(messages)
    protected = protected_indexes(result)
    seen = {}  # code text -> number (1-based) of the message holding its first copy

    for index, message in enumerate(result):
        content = message.get("content")
        if not isinstance(content, str):
            continue
        number = index + 1

        def replace(match, index=index, number=number):
            body = match.group(2)
            if count_tokens(body) < MIN_TOKENS:
                return match.group(0)
            key = body.strip()
            first = seen.get(key)
            if first is None:
                seen[key] = number
                return match.group(0)
            if index in protected:
                return match.group(0)
            return f"[code block omitted: identical to the one in message {first}]"

        message["content"] = _FENCE.sub(replace, content)
    return result