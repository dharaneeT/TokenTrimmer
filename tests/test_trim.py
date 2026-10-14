import copy

from tokentrim.tokens import count_tokens
from tokentrim.tools.trim import MIN_TOKENS, apply, trim_text

MARKER = "tokens trimmed from the middle"


def long_text():
    return "\n".join(f"line {i}: the server logged a warning about slow responses" for i in range(700))


def test_short_text_is_unchanged():
    assert trim_text("hello") == "hello"


def test_long_text_is_trimmed_with_a_marker():
    text = long_text()
    assert count_tokens(text) > MIN_TOKENS
    out = trim_text(text)
    assert MARKER in out
    assert out.startswith("line 0:")
    assert out.endswith("line 699: the server logged a warning about slow responses")
    assert count_tokens(out) < 800


def test_trimming_twice_equals_once():
    once = trim_text(long_text())
    assert trim_text(once) == once


def test_only_older_messages_are_trimmed():
    big = long_text()
    chat = [
        {"role": "system", "content": big},
        {"role": "user", "content": big},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": big},
    ]
    result = apply(chat)
    assert result[0] == chat[0]
    assert result[2] == chat[2]
    assert result[3] == chat[3]
    assert MARKER in result[1]["content"]


def test_input_is_not_modified():
    chat = [
        {"role": "user", "content": long_text()},
        {"role": "user", "content": "newest"},
    ]
    before = copy.deepcopy(chat)
    apply(chat)
    assert chat == before


def test_apply_twice_equals_once():
    chat = [
        {"role": "user", "content": long_text()},
        {"role": "user", "content": "newest"},
    ]
    once = apply(chat)
    assert apply(once) == once