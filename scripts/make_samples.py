"""Creates samples\\dup.json (a repeated code block) and samples\\long.json (one very long message)."""
import json
from pathlib import Path

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
SAMPLES.mkdir(exist_ok=True)

lines = "\n".join(f"total_{i} = compute_value({i}) + offset_{i}" for i in range(40))
block = "```python\n" + lines + "\n```"

dup = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Please review this code:\n\n" + block},
    {"role": "assistant", "content": "It looks fine. Do you want me to add tests?"},
    {"role": "user", "content": "Yes. Same code again, for reference:\n\n" + block},
    {"role": "assistant", "content": "Here are the tests."},
    {"role": "user", "content": "Thanks, one last question about naming."},
]

log = "\n".join(f"line {i}: the server logged a warning about slow responses" for i in range(700))
long = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Here is the full log:\n" + log},
    {"role": "assistant", "content": "Noted."},
    {"role": "user", "content": "Which line matters most?"},
]

for name, data in (("dup.json", dup), ("long.json", long)):
    path = SAMPLES / name
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("Wrote", path)