"""Step 4 (lossy): drop the oldest whole turns and leave one marker."""
import copy
import re

from ..messages import message_tokens, protected_indexes, total_tokens

NAME = "drop_old_turns"
KIND = "lossy"

_MARKER = re.compile(
    r"\[Earlier conversation removed to save tokens: (\d+) messages, about ([\d,]+) tokens\]"
)


def _marker_text(count, tokens):
    return f"[Earlier conversation removed to save tokens: {count} messages, about {tokens:,} tokens]"


def _find_marker(messages):
    """Return (index, message count, token count) of an earlier marker, or None."""
    for index, message in enumerate(messages):
        if message.get("role") == "user" and isinstance(message.get("content"), str):
            hit = _MARKER.fullmatch(message["content"])
            if hit:
                return index, int(hit.group(1)), int(hit.group(2).replace(",", ""))
    return None


def _units(messages):
    """Group message positions into turns. Each turn starts at a user message."""
    units = []
    current = []
    for index, message in enumerate(messages):
        if message.get("role") == "user" and current:
            units.append(current)
            current = []
        current.append(index)
    if current:
        units.append(current)
    return units


def _build(messages, dropped, marker_index, count, tokens):
    marker = {"role": "user", "content": _marker_text(count, tokens)}
    first = min(dropped)
    result = []
    for index, message in enumerate(messages):
        if index == marker_index:
            result.append(marker)
        elif index in dropped:
            if marker_index is None and index == first:
                result.append(marker)
        else:
            result.append(message)
    return result


def apply(messages, budget=None):
    if budget is None:
        raise ValueError("drop_old_turns needs a token budget (use --budget)")
    result = copy.deepcopy(messages)
    if total_tokens(result) <= budget:
        return result

    protected = protected_indexes(result)
    marker_index = None
    old_count = 0
    old_tokens = 0
    found = _find_marker(result)
    if found:
        marker_index, old_count, old_tokens = found
        protected.add(marker_index)

    dropped = set()
    dropped_tokens = 0
    for unit in _units(result):
        if any(index in protected for index in unit):
            continue
        dropped.update(unit)
        dropped_tokens += sum(message_tokens(result[index]) for index in unit)
        candidate = _build(result, dropped, marker_index,
                           old_count + len(dropped), old_tokens + dropped_tokens)
        if total_tokens(candidate) <= budget:
            break

    if not dropped:
        return result
    return _build(result, dropped, marker_index,
                  old_count + len(dropped), old_tokens + dropped_tokens)