import copy
from types import SimpleNamespace

import tokentrim.agent as agent
from tokentrim.agent import format_report, shrink


def big_chat():
    log = "\n".join(f"line {i}: the server logged a warning about slow responses" for i in range(700))
    return [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Q1\n" + log},
        {"role": "assistant", "content": "Noted.   "},
        {"role": "user", "content": "Q2 question"},
        {"role": "assistant", "content": "A2"},
        {"role": "user", "content": "What is the newest question?"},
    ]


def test_already_under_budget_changes_nothing():
    chat = big_chat()
    result = shrink(chat, 1_000_000)
    assert result.status == "done"
    assert result.steps == []
    assert result.messages == chat


def test_shrinks_to_budget_and_keeps_protected_messages():
    chat = big_chat()
    before = copy.deepcopy(chat)
    result = shrink(chat, 2000)
    assert chat == before
    assert result.status == "done"
    assert result.end_tokens <= 2000 < result.start_tokens
    assert result.messages[0] == chat[0]
    assert result.messages[-1] == chat[-1]
    assert any(s.name == "trim_long_message" and s.accepted for s in result.steps)


def test_stops_when_no_safe_step_is_left():
    chat = big_chat()
    result = shrink(chat, 5)
    assert result.status == "stopped"
    assert result.end_tokens > 5
    assert result.messages[0] == chat[0]
    assert result.messages[-1] == chat[-1]


def test_a_failing_step_is_skipped_and_the_loop_continues(monkeypatch):
    def boom(messages, budget=None):
        raise RuntimeError("boom")

    broken = SimpleNamespace(NAME="trim_long_message", KIND="lossy", apply=boom)
    monkeypatch.setitem(agent.TOOLS, "trim_long_message", broken)
    result = shrink(big_chat(), 2000)
    trim = [s for s in result.steps if s.name == "trim_long_message"][0]
    assert not trim.accepted and "error" in trim.note
    assert result.status == "done"


def test_agent_failure_returns_original_text(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(agent, "_run", boom)
    chat = big_chat()
    result = shrink(chat, 2000)
    assert result.status == "failed"
    assert result.messages == chat
    assert "original text is returned unchanged" in format_report(result)


def test_at_most_max_steps():
    result = shrink(big_chat(), 5, max_steps=2)
    assert len(result.steps) == 2


def test_report_format():
    report = format_report(shrink(big_chat(), 2000))
    assert report.startswith("Budget 2,000 tokens.  Start: ")
    assert report.splitlines()[-1].startswith("Done:")