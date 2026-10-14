"""Day 10: ask the local model to shorten one text and time it.

Run:  python scripts\\try_summary.py
      (uses the built-in paragraph)

      python scripts\\try_summary.py file.txt
      (uses your own text file)
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from tokentrim.llm import LLMError, is_available  # noqa: E402
from tokentrim.tokens import count_tokens  # noqa: E402
from tokentrim.tools.summarize import (  # noqa: E402
    MAX_TOKENS,
    summarize_segment,
)

SAMPLE = r"""Last week the team moved the billing database from the old server to the new one. The move started on Monday morning and the first plan was to finish by Tuesday night, but the export of the invoices table took much longer than expected because the table had grown to more than 40 million rows. On Wednesday the team split the export into smaller batches, which made it faster, and they also found that the file C:\billing\settings.ini still pointed to the old server. After that was fixed the import finished on Thursday. Friday was used to compare row counts, run the monthly report once on each server, and check that the nightly backup job works on the new machine. The only open problem is that the report on the new server runs about twelve percent slower, and the team plans to look at the indexes next week before switching off the old server for good."""


def main():
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text(encoding="utf-8-sig")
    else:
        text = SAMPLE

    before = count_tokens(text)

    print(
        "Ollama ready with the configured model:",
        is_available(),
    )

    if before > MAX_TOKENS:
        print(
            f"Note: {before:,} tokens is over {MAX_TOKENS:,}; "
            "the agent would skip this text."
        )

    started = time.perf_counter()

    try:
        summary = summarize_segment(text)
    except LLMError as error:
        print("Failed:", error)
        return

    seconds = time.perf_counter() - started
    after = count_tokens(summary)

    print(f"Tokens: {before:,} -> {after:,} (estimate)")
    print(
        f"Time: {seconds:.1f} seconds "
        "(the first call also loads the model, so it is slower)"
    )
    print("\nSummary:\n" + summary)


if __name__ == "__main__":
    main()