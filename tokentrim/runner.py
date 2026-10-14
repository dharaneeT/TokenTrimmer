"""One place that runs the agent for every entry point (command line, paste page, proxy).

It also records every run in the ledger."""
import logging
import time

from . import ledger
from .agent import shrink

log = logging.getLogger("tokentrim")


def run_agent(messages, budget, source, use_ai=False):
    """Returns (result, run_id). run_id is None if the ledger could not be written."""
    started = time.perf_counter()
    result = shrink(messages, budget, use_ai=use_ai)
    duration_ms = int((time.perf_counter() - started) * 1000)
    try:
        run_id = ledger.record_run(result, source, duration_ms)
    except Exception as error:
        log.warning("Could not record the run in the ledger: %s", error)
        run_id = None
    return result, run_id