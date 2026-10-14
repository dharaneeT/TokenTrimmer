"""Safety net for every step: protected messages never change, the input is never
modified, and a second run changes nothing."""
import copy

import pytest

from tokentrim.tools import TOOLS

# summarize_prose needs the AI model; it has its own tests with a fake model.
NAMES = [name for name in sorted(TOOLS) if name != "summarize_prose"]


def messy_chat():
    filler = "word   \n\n\n\n" * 400
    block = "```python\n" + "\n".join(f"v_{i} = f({i})" for i in range(60)) + "\n```"
    return [
        {"role": "system", "content": "sys " + filler},
        {"role": "user", "content": "Q1 " + filler + block},
        {"role": "assistant", "content": "A1 " + filler},
        {"role": "user", "content": "Q2\n" + block},
        {"role": "assistant", "content": "A2 " + filler},
        {"role": "user", "content": "newest " + filler + block},
    ]


@pytest.mark.parametrize("name", NAMES)
def test_system_and_newest_message_are_identical(name):
    chat = messy_chat()
    result = TOOLS[name].apply(chat, budget=300)
    assert result[0] == chat[0]
    assert result[-1] == chat[-1]


@pytest.mark.parametrize("name", NAMES)
def test_input_unchanged_and_second_run_changes_nothing(name):
    chat = messy_chat()
    before = copy.deepcopy(chat)
    once = TOOLS[name].apply(chat, budget=300)
    assert chat == before
    assert TOOLS[name].apply(once, budget=300) == once