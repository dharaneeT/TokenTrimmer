from fastapi.testclient import TestClient

from tokentrim.server import app

client = TestClient(app)

LOG = "\n".join(f"line {i}: the server logged a warning about slow responses" for i in range(700))


def test_home_page_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "tokentrim" in response.text


def test_shrinks_a_pasted_chat():
    text = f"### user\nHere is a log:\n{LOG}\n\n### assistant\nNoted.\n\n### user\nWhat now?"
    response = client.post("/api/shrink", json={"text": text, "budget": 1000})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "done"
    assert data["end_tokens"] <= 1000 < data["start_tokens"]
    assert "tokens trimmed from the middle" in data["output"]
    assert data["output"].rstrip().endswith("What now?")


def test_plain_text_with_a_question():
    response = client.post("/api/shrink", json={"text": LOG, "question": "Summarize", "budget": 1000})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "done"
    assert data["output"].rstrip().endswith("Summarize")


def test_plain_text_without_a_question_is_rejected():
    response = client.post("/api/shrink", json={"text": "just some text", "budget": 100})
    assert response.status_code == 400


def test_empty_text_is_rejected():
    response = client.post("/api/shrink", json={"text": "   ", "budget": 100})
    assert response.status_code == 400