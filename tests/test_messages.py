import json

import pytest

from tokentrim.messages import (
    load_messages,
    parse_text_chat,
    protected_indexes,
    save_messages,
)
from tokentrim.tokens import count_tokens


def test_hello_world_is_two_tokens():
    assert count_tokens("hello world") == 2


def test_empty_text_is_zero_tokens():
    assert count_tokens("") == 0


def test_parse_text_chat_splits_by_role():
    text = "### system\nBe brief.\n\n### user\nHi there\n"
    assert parse_text_chat(text) == [
        {"role": "system", "content": "Be brief."},
        {"role": "user", "content": "Hi there"},
    ]


def test_parse_text_chat_needs_headers():
    with pytest.raises(ValueError):
        parse_text_chat("just some text")


def test_save_and_load_round_trip(tmp_path):
    messages = [{"role": "user", "content": "hello"}]
    path = tmp_path / "chat.json"
    save_messages(path, messages)
    assert load_messages(path) == messages


def test_load_accepts_messages_key(tmp_path):
    path = tmp_path / "chat.json"
    path.write_text(json.dumps({"messages": [{"role": "user", "content": "x"}]}), encoding="utf-8")
    assert load_messages(path) == [{"role": "user", "content": "x"}]


def test_load_rejects_unknown_role(tmp_path):
    path = tmp_path / "chat.json"
    path.write_text(json.dumps([{"role": "robot", "content": "x"}]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_messages(path)


def test_protected_indexes():
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "1"}]},
        {"role": "user", "content": "b"},
        {"role": "user", "content": "newest"},
    ]
    assert protected_indexes(messages) == {0, 2, 4}