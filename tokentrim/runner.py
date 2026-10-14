"""One place that runs the agent for every entry point (command line, paste page, proxy)."""
from .agent import shrink


def run_agent(messages, budget, source, use_ai=False):
    """Returns (result, run_id). run_id stays None until the ledger exists (day 9)."""
    return shrink(messages, budget, use_ai=use_ai), None