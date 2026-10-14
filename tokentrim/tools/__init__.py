"""Registry of steps. Each step is a module with NAME, KIND and apply(messages, budget=None).

The list below is the fixed order the agent will use. A step that does not
exist yet (its file is not written) is skipped, so this file never changes.
"""
import importlib

_ORDER = ["normalize", "dedupe", "trim", "window", "summarize"]

TOOLS = {}

for _name in _ORDER:
    _module_name = f"tokentrim.tools.{_name}"
    try:
        _module = importlib.import_module(_module_name)
    except ModuleNotFoundError as error:
        if error.name != _module_name:
            raise
        continue
    TOOLS[_module.NAME] = _module