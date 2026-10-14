"""Settings from config.toml (project root), with safe defaults."""
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "ollama": {
        "url": "http://127.0.0.1:11434",
        "model": "qwen2.5-coder:3b",
        "timeout_seconds": 120,
        "num_ctx": 4096,
    }
}


def load_config():
    config = {section: dict(values) for section, values in DEFAULTS.items()}
    path = ROOT / "config.toml"
    if path.exists():
        data = tomllib.loads(path.read_text(encoding="utf-8-sig"))
        for section, values in data.items():
            if section in config and isinstance(values, dict):
                config[section].update(values)
    return config