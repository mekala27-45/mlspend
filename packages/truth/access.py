import inspect
from pathlib import Path
from typing import Any

from packages.core.io import read_json


def read_truth(path: Path) -> dict[str, Any]:
    caller = inspect.currentframe()
    parent = caller.f_back if caller else None
    name = str(parent.f_globals.get("__name__", "")) if parent else ""
    if not name.startswith("packages.evaluation."):
        raise PermissionError("Only evaluation may open simulator truth")
    value: dict[str, Any] = read_json(path)
    return value
