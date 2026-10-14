from fastapi.testclient import TestClient

from tokentrim import ledger
from tokentrim.runner import run_agent
from tokentrim.server import app

LOG = "\n".join(f"line {i}: the server logged a warning about slow responses" for i in range(700))


def chat():
    return [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Q1\n" + LOG},
        {"role": "assistant", "content": "Noted."},
        {"role": "user", "content": "What now?"},
    ]


def test_empty_ledger():
    data = ledger.stats()
    assert data["runs"] == 0
    assert data["recent"] == []


def test_a_run_is_recorded():
    result, run_id = run_agent(chat(), 1000, "test")
    assert run_id == 1
    data = ledger.stats()
    assert data["runs"] == 1
    assert data["start_total"] == result.start_tokens
    assert data["end_total"] == result.end_tokens
    assert data["recent"][0]["source"] == "test"
    assert data["recent"][0]["steps"] == len(result.steps)


def test_a_ledger_failure_does_not_break_the_run(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(ledger, "record_run", boom)
    result, run_id = run_agent(chat(), 1000, "test")
    assert run_id is None
    assert result.status == "done"


def test_stats_endpoint_after_a_web_run():
    client = TestClient(app)
    text = f"### user\nQ1\n{LOG}\n\n### assistant\nNoted.\n\n### user\nWhat now?"
    assert client.post("/api/shrink", json={"text": text, "budget": 1000}).status_code == 200
    data = client.get("/api/stats").json()
    assert data["runs"] == 1
    assert data["recent"][0]["source"] == "web"