"""Token counting. These are estimates made with tiktoken (cl100k_base)."""
import tiktoken

_encoder = None


def _get_encoder():
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


def encode(text):
    return _get_encoder().encode(text, disallowed_special=())


def decode(tokens):
    return _get_encoder().decode(tokens)


def count_tokens(text):
    if not text:
        return 0
    return len(encode(text))