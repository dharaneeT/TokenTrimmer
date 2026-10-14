"""Step 1: remove colour codes, trailing spaces and extra blank lines. Keeps indentation."""
import copy
import re

from ..messages import protected_indexes

NAME = "normalize_whitespace"
KIND = "lossless"

_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_TRAILING = re.compile(r"[ \t]+$", re.MULTILINE)
_BLANK_RUNS = re.compile(r"\n{3,}")


def normalize_text(text):
    text = _ANSI.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _TRAILING.sub("", text)
    text = _BLANK_RUNS.sub("\n\n", text)
    return text.strip("\n")


def apply(messages, budget=None):
    result = copy.deepcopy(messages)
    protected = protected_indexes(result)
    for index, message in enumerate(result):
        if index not in protected:
            message["content"] = normalize_text(message["content"])
    return result