import copy

from tokentrim.tools.normalize import apply, normalize_text


def make_chat():
    return [
        {"role": "system", "content": "sys   \n\n\n\nrules   "},
        {"role": "user", "content": "old   \n\n\n\nmessage   "},
        {"role": "assistant", "content": "reply  "},
        {"role": "user", "content": "newest   \n\n\n\nmessage   "},
    ]


def test_removes_colour_codes():
    assert normalize_text("\x1b[31mERROR\x1b[0m failed") == "ERROR failed"


def test_removes_trailing_spaces_and_tabs():
    assert normalize_text("a   \nb\t\nc") == "a\nb\nc"


def test_keeps_indentation():
    code = "def f():\n    return 1"
    assert normalize_text(code) == code


def test_collapses_blank_lines():
    assert normalize_text("a\n\n\n\n\nb") == "a\n\nb"


def test_converts_windows_line_endings():
    assert normalize_text("a\r\nb\r\n") == "a\nb"


def test_text_function_is_idempotent():
    text = "\x1b[1mx\x1b[0m  \n\n\n\n  y   \r\n"
    once = normalize_text(text)
    assert normalize_text(once) == once


def test_only_older_messages_change():
    chat = make_chat()
    result = apply(chat)
    assert result[0] == chat[0]
    assert result[3] == chat[3]
    assert result[1]["content"] == "old\n\nmessage"
    assert result[2]["content"] == "reply"


def test_input_is_not_modified():
    chat = make_chat()
    before = copy.deepcopy(chat)
    apply(chat)
    assert chat == before


def test_apply_twice_equals_once():
    once = apply(make_chat())
    assert apply(once) == once


def test_tool_messages_are_untouched():
    chat = [
        {"role": "user", "content": "q"},
        {"role": "tool", "content": "out   \n\n\n\n", "tool_call_id": "1"},
        {"role": "user", "content": "newest"},
    ]
    assert apply(chat)[1] == chat[1]