"""Command line for tokentrim."""
import argparse
import sys
from pathlib import Path

from .messages import (
    content_text,
    load_messages,
    message_tokens,
    parse_text_chat,
    save_messages,
    total_tokens,
)
from .tools import TOOLS


def _preview(text, limit=1500):
    if len(text) <= limit:
        return repr(text)
    half = limit // 2
    hidden = len(text) - limit
    return f"{text[:half]!r} ... [{hidden:,} characters not shown] ... {text[-half:]!r}"


def cmd_count(args):
    messages = load_messages(args.file)
    print(f"{'#':>3}  {'role':<10} {'tokens':>8}  preview")
    for number, message in enumerate(messages, 1):
        preview = content_text(message).replace("\n", " ")[:50]
        print(f"{number:>3}  {message['role']:<10} {message_tokens(message):>8,}  {preview}")
    print(f"Total: {total_tokens(messages):,} tokens in {len(messages)} messages "
          "(estimate, tiktoken cl100k_base)")


def cmd_convert(args):
    text = Path(args.source).read_text(encoding="utf-8-sig")
    messages = parse_text_chat(text)
    save_messages(args.target, messages)
    print(f"Wrote {len(messages)} messages to {args.target}")


def cmd_apply(args):
    if args.step not in TOOLS:
        names = ", ".join(sorted(TOOLS)) or "(none yet)"
        raise ValueError(f"unknown step '{args.step}'. Available steps: {names}")
    messages = load_messages(args.file)
    result = TOOLS[args.step].apply(messages, budget=args.budget)
    before_total = total_tokens(messages)
    after_total = total_tokens(result)
    same_length = len(result) == len(messages)

    if same_length:
        print(f"{'#':>3}  {'role':<10} {'before':>8} {'after':>8}")
        for number, (old, new) in enumerate(zip(messages, result), 1):
            print(f"{number:>3}  {old['role']:<10} {message_tokens(old):>8,} {message_tokens(new):>8,}")
    else:
        print(f"Messages: {len(messages)} -> {len(result)}")
    print(f"Total: {before_total:,} -> {after_total:,} tokens (saved {before_total - after_total:,})")

    if args.show is not None:
        if not 1 <= args.show <= len(messages):
            raise ValueError(f"--show must be between 1 and {len(messages)}")
        if not same_length:
            print("(--show needs the step to keep the same number of messages)")
        else:
            index = args.show - 1
            print(f"\nMessage {args.show} before: {_preview(content_text(messages[index]))}")
            print(f"Message {args.show} after:  {_preview(content_text(result[index]))}")

    if args.out:
        save_messages(args.out, result)
        print(f"\nSaved result to {args.out}")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="tokentrim", description="Shrink long chat prompts.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_count = sub.add_parser("count", help="show tokens per message")
    p_count.add_argument("file", help="a chat .json file")
    p_count.set_defaults(func=cmd_count)

    p_convert = sub.add_parser("convert", help="turn a ### text chat into a .json chat")
    p_convert.add_argument("source", help="the .txt file")
    p_convert.add_argument("target", help="the .json file to create")
    p_convert.set_defaults(func=cmd_convert)

    p_apply = sub.add_parser("apply", help="run one step on a chat and show the effect")
    p_apply.add_argument("step", help="step name, for example normalize_whitespace")
    p_apply.add_argument("file", help="a chat .json file")
    p_apply.add_argument("--budget", type=int, default=None, help="token budget (some steps need it)")
    p_apply.add_argument("--show", type=int, default=None, help="print message N before and after")
    p_apply.add_argument("--out", default=None, help="save the result to this .json file")
    p_apply.set_defaults(func=cmd_apply)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0