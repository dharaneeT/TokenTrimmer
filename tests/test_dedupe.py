import copy

from tokentrim.tools.dedupe import apply


def make_block(size=40):
    body = "\n".join(f"total_{i} = compute_value({i}) + offset_{i}" for i in range(size))
    return "```python\n" + body + "\n```"


def make_chat():
    block = make_block()
    return [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "Here:\n\n" + block},
        {"role": "assistant", "content": "Thanks"},
        {"role": "user", "content": "Again:\n\n" + block},
        {"role": "user", "content": "final question"},
    ]


def test_second_copy_is_replaced_and_first_stays():
    chat = make_chat()
    result = apply(chat)
    assert result[1] == chat[1]
    assert result[3]["content"] == (
        "Again:\n\n[code block omitted: identical to the one in message 2]"
    )


def test_short_blocks_are_kept():
    short = "```python\nx = 1\n```"
    chat = [
        {"role": "user", "content": short},
        {"role": "assistant", "content": short},
        {"role": "user", "content": "newest"},
    ]
    assert apply(chat) == chat


def test_different_blocks_are_kept():
    chat = [
        {"role": "user", "content": make_block(40)},
        {"role": "assistant", "content": make_block(41)},
        {"role": "user", "content": "newest"},
    ]
    assert apply(chat) == chat


def test_newest_message_is_never_changed():
    block = make_block()
    chat = [
        {"role": "user", "content": block},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": block},
    ]
    result = apply(chat)
    assert result[2] == chat[2]


def test_input_is_not_modified():
    chat = make_chat()
    before = copy.deepcopy(chat)
    apply(chat)
    assert chat == before


def test_apply_twice_equals_once():
    once = apply(make_chat())
    assert apply(once) == once