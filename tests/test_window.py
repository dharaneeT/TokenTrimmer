import copy

import pytest

from tokentrim.messages import total_tokens
from tokentrim.tools.window import apply

FILLER = "word " * 300  # about 300 tokens


def make_chat():
    return [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "Q1 " + FILLER},
        {"role": "assistant", "content": "A1 " + FILLER},
        {"role": "user", "content": "Q2 " + FILLER},
        {"role": "assistant", "content": "A2 " + FILLER},
        {"role": "user", "content": "Q3 newest"},
    ]


def test_needs_a_budget():
    with pytest.raises(ValueError):
        apply(make_chat())


def test_under_budget_is_unchanged():
    chat = make_chat()
    assert apply(chat, budget=10000) == chat


def test_drops_oldest_turn_first_and_leaves_one_marker():
    chat = make_chat()
    result = apply(chat, budget=700)
    assert len(result) == 5
    assert result[0] == chat[0]
    assert result[-1] == chat[-1]
    assert "Earlier conversation removed" in result[1]["content"]
    assert "2 messages" in result[1]["content"]
    assert result[2] == chat[3]  # Q2 is kept
    assert all("Q1" not in m["content"] for m in result)
    assert total_tokens(result) <= 700


def test_drops_more_turns_when_needed():
    result = apply(make_chat(), budget=100)
    assert len(result) == 3
    assert "4 messages" in result[1]["content"]
    assert total_tokens(result) <= 100


def test_tool_call_and_reply_are_never_split():
    chat = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "Q1 " + FILLER},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1"}]},
        {"role": "tool", "content": "result " + FILLER, "tool_call_id": "c1"},
        {"role": "assistant", "content": "A1 " + FILLER},
        {"role": "user", "content": "Q2 " + FILLER},
        {"role": "assistant", "content": "A2 " + FILLER},
        {"role": "user", "content": "newest"},
    ]
    result = apply(chat, budget=1000)
    assert chat[2] in result and chat[3] in result
    assert result.index(chat[3]) == result.index(chat[2]) + 1
    assert chat[5] not in result  # the plain turn was dropped instead


def test_second_run_with_smaller_budget_keeps_one_marker():
    first = apply(make_chat(), budget=700)
    second = apply(first, budget=100)
    markers = [m for m in second if "Earlier conversation removed" in m["content"]]
    assert len(markers) == 1
    assert "4 messages" in markers[0]["content"]


def test_apply_twice_equals_once():
    for budget in (700, 100):
        once = apply(make_chat(), budget=budget)
        assert apply(once, budget=budget) == once


def test_input_is_not_modified():
    chat = make_chat()
    before = copy.deepcopy(chat)
    apply(chat, budget=100)
    assert chat == before