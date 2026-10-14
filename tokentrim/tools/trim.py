"""Step 3 (lossy): in an old message over 1,500 tokens, keep the start and end, mark the cut."""
import copy

from ..messages import protected_indexes
from ..tokens import decode, encode

NAME = "trim_long_message"
KIND = "lossy"
MIN_TOKENS = 1500
HEAD_TOKENS = 400
TAIL_TOKENS = 300


def trim_text(text):
    tokens = encode(text)
    if len(tokens) <= MIN_TOKENS:
        return text
    removed = len(tokens) - HEAD_TOKENS - TAIL_TOKENS
    head = decode(tokens[:HEAD_TOKENS])
    tail = decode(tokens[-TAIL_TOKENS:])
    marker = f"\n\n[... {removed:,} tokens trimmed from the middle of this message ...]\n\n"
    return head + marker + tail


def apply(messages, budget=None):
    result = copy.deepcopy(messages)
    protected = protected_indexes(result)
    for index, message in enumerate(result):
        if index not in protected:
            message["content"] = trim_text(message["content"])
    return result