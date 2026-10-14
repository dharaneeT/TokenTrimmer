"""Web server: serves the paste page and its API."""
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import ledger
from .agent import format_report
from .messages import content_text, parse_text_chat
from .runner import run_agent

WEB = Path(__file__).resolve().parent / "web"

app = FastAPI(title="tokentrim")
app.mount("/static", StaticFiles(directory=WEB), name="static")


class ShrinkRequest(BaseModel):
    text: str
    question: str = ""
    budget: int = Field(default=3000, ge=50, le=1_000_000)


def messages_to_text(messages):
    return "\n\n".join(f"### {m['role']}\n{content_text(m)}" for m in messages) + "\n"


@app.get("/")
def home():
    return FileResponse(WEB / "index.html")


@app.post("/api/shrink")
def api_shrink(req: ShrinkRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Paste some text first.")
    try:
        messages = parse_text_chat(req.text)
    except ValueError:
        messages = [{"role": "user", "content": req.text}]
    if req.question.strip():
        messages.append({"role": "user", "content": req.question.strip()})
    if len(messages) < 2:
        raise HTTPException(
            status_code=400,
            detail="Add your latest question in the second box. It is kept exactly, "
                   "and the pasted text above it can then be shrunk.",
        )

    result, run_id = run_agent(messages, req.budget, "web")
    report = format_report(result)
    return {
        "status": result.status,
        "budget": result.budget,
        "start_tokens": result.start_tokens,
        "end_tokens": result.end_tokens,
        "saved": result.start_tokens - result.end_tokens,
        "steps": [asdict(step) for step in result.steps],
        "verdict": report.splitlines()[-1],
        "report": report,
        "output": messages_to_text(result.messages),
        "run_id": run_id,
    }


@app.get("/api/stats")
def api_stats(limit: int = 10):
    return ledger.stats(limit=max(1, min(limit, 100)))