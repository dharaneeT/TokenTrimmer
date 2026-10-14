"""Prints the ledger totals and the latest runs.  Run:  python -m tokentrim.stats"""
import sys

from .ledger import stats


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    data = stats(limit=10)
    start, end = data["start_total"], data["end_total"]
    pct = round(100 * (start - end) / start) if start else 0
    print(f"Runs: {data['runs']}   Tokens before: {start:,}   after: {end:,}   "
          f"saved: {start - end:,} ({pct}%)")
    print("All numbers are estimates made with tiktoken.")
    if not data["recent"]:
        print("No runs recorded yet.")
        return
    print(f"\n{'run':>4}  {'time (UTC)':<19}  {'source':<6} {'budget':>8} {'before':>8} "
          f"{'after':>8}  {'status':<8} {'steps':>5} {'ms':>6}")
    for run in data["recent"]:
        when = run["created_at"].replace("T", " ")[:19]
        print(f"{run['id']:>4}  {when:<19}  {run['source']:<6} {run['budget']:>8,} "
              f"{run['start_tokens']:>8,} {run['end_tokens']:>8,}  {run['status']:<8} "
              f"{run['steps']:>5} {run['duration_ms']:>6,}")


if __name__ == "__main__":
    main()