"""Step 5 (lossy, uses AI): shorten long prose in old messages with the local model.

Never touches code blocks. If the model is missing or slow, the step is skipped."""
import copy
import re

from .. import llm
from ..messages import protected_indexes
from ..tokens import count_tokens

NAME = "summarize_prose"
KIND = "lossy, uses AI"
USES_AI = True

MIN_TOKENS = 200   # shorter prose is not worth a model call
MAX_TOKENS = 1500  # longer prose is left to trim_long_message (too slow on a CPU)

SYSTEM = (
    "You shorten text. Keep every file name, path, URL, number, command, name in "
    "backticks and error message exactly as written. Do not add anything that is "
    "not in the text. Write in the same language as the text. "
    "Reply with only the shortened text."
)

_FENCE = re.compile(
    r"^(```[^\n]*)\n(.*?)\n?^```[ \t\r]*$",
    re.MULTILINE | re.DOTALL,
)


def split_segments(text):
    """Split text into ('prose', ...) and ('code', ...) pieces.

    Joining the pieces gives the original text back.
    """
    segments = []
    position = 0

    for match in _FENCE.finditer(text):
        if match.start() > position:
            segments.append(("prose", text[position:match.start()]))

        segments.append(("code", match.group(0)))
        position = match.end()

    if position < len(text):
        segments.append(("prose", text[position:]))

    return segments


def summarize_segment(text, ask=None):
    ask = ask or llm.chat

    prompt = "Shorten this text to about half its length:\n\n" + text.strip()

    return ask(prompt, system=SYSTEM).strip()


def _shorten(segment, ask):
    tokens = count_tokens(segment)

    if tokens < MIN_TOKENS or tokens > MAX_TOKENS:
        return segment

    summary = summarize_segment(segment, ask)

    if not summary or count_tokens(summary) > tokens * 0.8:
        return segment  # not clearly shorter: keep the original

    lead = segment[: len(segment) - len(segment.lstrip())]
    trail = segment[len(segment.rstrip()):]

    return lead + summary + trail


def _summarize_message(text, ask):
    parts = []

    for kind, segment in split_segments(text):
        if kind == "prose":
            parts.append(_shorten(segment, ask))
        else:
            parts.append(segment)

    return "".join(parts)


def apply(messages, budget=None, ask=None):
    result = copy.deepcopy(messages)
    protected = protected_indexes(result)
    changed = False

    try:
        for index, message in enumerate(result):
            if index in protected:
                continue

            new_text = _summarize_message(message["content"], ask)

            if new_text != message["content"]:
                message["content"] = new_text
                changed = True

    except llm.LLMError:
        if not changed:
            raise  # nothing done: the agent records this step as skipped

    return result