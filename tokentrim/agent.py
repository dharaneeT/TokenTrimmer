"""The agent loop: measure, choose, act, check, repeat.

Stops when the text is under the budget or no safe step is left."""
import copy
from dataclasses import dataclass, field

from .messages import protected_indexes, total_tokens
from .tools import TOOLS

MAX_STEPS = 8


@dataclass
class Step:
    name: str
    kind: str
    before: int
    after: int
    accepted: bool
    note: str


@dataclass
class Result:
    messages: list
    budget: int
    start_tokens: int
    end_tokens: int
    status: str  # "done", "stopped" or "failed"
    steps: list = field(default_factory=list)
    note: str = ""


def protected_messages(messages):
    return [messages[index] for index in sorted(protected_indexes(messages))]


def _run(original, budget, max_steps, use_ai):
    start = total_tokens(original)
    current = copy.deepcopy(original)
    tokens = start
    steps = []
    if tokens <= budget:
        return Result(current, budget, start, tokens, "done", steps,
                      "already under budget, nothing changed")

    keep = protected_messages(original)
    for tool in list(TOOLS.values()):  # fixed order: safest steps first
        if len(steps) >= max_steps or tokens <= budget:
            break
        if getattr(tool, "USES_AI", False) and not use_ai:
            continue
        try:
            candidate = tool.apply(current, budget=budget)
        except Exception as error:
            steps.append(Step(tool.NAME, tool.KIND, tokens, tokens, False,
                              f"skipped, error: {error}"))
            continue
        after = total_tokens(candidate)
        if protected_messages(candidate) != keep:
            steps.append(Step(tool.NAME, tool.KIND, tokens, tokens, False,
                              "undone: a protected message changed"))
            continue
        if after >= tokens:
            steps.append(Step(tool.NAME, tool.KIND, tokens, tokens, False,
                              "no gain, not kept"))
            continue
        steps.append(Step(tool.NAME, tool.KIND, tokens, after, True, tool.KIND))
        current, tokens = candidate, after

    if tokens <= budget:
        return Result(current, budget, start, tokens, "done", steps, "under budget")
    return Result(current, budget, start, tokens, "stopped", steps, "no safe step left")


def shrink(messages, budget, max_steps=MAX_STEPS, use_ai=False):
    original = copy.deepcopy(messages)
    try:
        return _run(original, budget, max_steps, use_ai)
    except Exception as error:  # fail-safe: give back the original text
        try:
            tokens = total_tokens(original)
        except Exception:
            tokens = 0
        return Result(original, budget, tokens, tokens, "failed", [], f"agent error: {error}")


def format_report(result):
    lines = [f"Budget {result.budget:,} tokens.  Start: {result.start_tokens:,}"]
    for number, step in enumerate(result.steps, 1):
        change = step.after - step.before
        lines.append(f"{number:<3}{step.name:<22}{change:>8,}{step.after:>9,}   {step.note}")
    if result.status == "done":
        if result.steps:
            lines.append(f"Done: {result.end_tokens:,} is under the {result.budget:,} budget")
        else:
            lines.append(f"Done: {result.note}")
    elif result.status == "stopped":
        lines.append(f"Stopped: no safe step left. {result.end_tokens:,} tokens, "
                     f"still over the {result.budget:,} budget")
    else:
        lines.append(f"Agent error ({result.note}). Your original text is returned unchanged.")
    return "\n".join(lines)