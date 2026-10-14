import copy

import httpx
import pytest

from tokentrim import llm
from tokentrim.llm import LLMError
from tokentrim.tools.summarize import apply, split_segments

SENTENCE = (
    "The migration started on Monday and the team moved "
    "the database to the new server."
)
PROSE = " ".join([SENTENCE] * 20)  # about 340 tokens


def fake_ask(prompt, system=None):
    return "Short summary."


def test_split_segments_round_trip():
    text = "a\n```py\ncode\n```\nb"

    segments = split_segments(text)

    assert segments == [
        ("prose", "a\n"),
        ("code", "```py\ncode\n```"),
        ("prose", "\nb"),
    ]

    assert "".join(part for _, part in segments) == text


def test_prose_is_shortened_and_code_is_kept():
    chat = [
        {"role": "system", "content": "sys"},
        {
            "role": "user",
            "content": (
                "Intro\n\n"
                + PROSE
                + "\n\n```python\nx = 1\n```\n\nbye"
            ),
        },
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "newest"},
    ]

    result = apply(chat, ask=fake_ask)

    assert result[1]["content"] == (
        "Short summary.\n\n```python\nx = 1\n```\n\nbye"
    )


def test_short_prose_is_not_sent_to_the_model():
    def never(prompt, system=None):
        raise AssertionError("the model should not be called")

    chat = [
        {"role": "user", "content": "short text"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "newest"},
    ]

    assert apply(chat, ask=never) == chat


def test_too_long_prose_is_left_alone():
    def never(prompt, system=None):
        raise AssertionError("the model should not be called")

    huge = " ".join([SENTENCE] * 120)  # well over 1,500 tokens

    chat = [
        {"role": "user", "content": huge},
        {"role": "user", "content": "newest"},
    ]

    assert apply(chat, ask=never) == chat


def test_only_older_messages_are_sent():
    calls = []

    def ask(prompt, system=None):
        calls.append(prompt)
        return "Short summary."

    chat = [
        {"role": "system", "content": PROSE},
        {"role": "user", "content": PROSE},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": PROSE},
    ]

    result = apply(chat, ask=ask)

    assert len(calls) == 1
    assert result[0] == chat[0]
    assert result[3] == chat[3]


def test_a_summary_that_is_not_shorter_is_ignored():
    chat = [
        {"role": "user", "content": PROSE},
        {"role": "user", "content": "newest"},
    ]

    assert apply(chat, ask=lambda prompt, system=None: PROSE) == chat


def test_error_with_no_progress_is_raised():
    def broken(prompt, system=None):
        raise LLMError("Ollama is off")

    chat = [
        {"role": "user", "content": PROSE},
        {"role": "user", "content": "newest"},
    ]

    with pytest.raises(LLMError):
        apply(chat, ask=broken)


def test_progress_is_kept_when_a_later_call_fails():
    calls = []

    def flaky(prompt, system=None):
        calls.append(1)

        if len(calls) > 1:
            raise LLMError("timeout")

        return "Short summary."

    chat = [
        {"role": "user", "content": PROSE},
        {"role": "assistant", "content": PROSE},
        {"role": "user", "content": "newest"},
    ]

    result = apply(chat, ask=flaky)

    assert result[0]["content"] == "Short summary."
    assert result[1] == chat[1]


def test_input_is_not_modified():
    chat = [
        {"role": "user", "content": PROSE},
        {"role": "user", "content": "newest"},
    ]

    before = copy.deepcopy(chat)

    apply(chat, ask=fake_ask)

    assert chat == before


def test_llm_wraps_connection_errors(monkeypatch):
    def boom(*args, **kwargs):
        raise httpx.ConnectError("no server")

    monkeypatch.setattr(httpx, "post", boom)

    with pytest.raises(LLMError):
        llm.chat("hi")


def test_is_available_is_false_when_ollama_is_off(monkeypatch):
    def boom(*args, **kwargs):
        raise httpx.ConnectError("no server")

    monkeypatch.setattr(httpx, "get", boom)

    assert llm.is_available() is False