from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from pathlib import Path


def text_gate(files: Mapping[str, str], *, check_wording: bool = True) -> None:
    if not files or not any(value.strip() for value in files.values()):
        raise ValueError("No content was scanned")
    banned = re.compile(r"\b(seamless|cutting-edge|game changer|delve|synergy)\b", re.I)
    secret = re.compile(
        r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|postgres(?:ql)?://[^\s:]+:[^\s@]+@)"
    )
    for name, content in files.items():
        if chr(0x2014) in content:
            raise ValueError(f"Em dash in {name}")
        if check_wording and banned.search(content):
            raise ValueError(f"Banned wording in {name}")
        if secret.search(content):
            raise ValueError(f"Possible credential in {name}")


def import_boundary(root: Path) -> None:
    files = [
        file
        for name in ("allocation", "unit", "forecast", "detect", "optimize")
        for file in (root / name).glob("*.py")
    ]
    expanded = root / "expansion" / "analysis.py"
    if expanded.exists():
        files.append(expanded)
    if not files:
        raise ValueError("No method modules found")
    for file in files:
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and "truth" in node.module.split(".")
            ):
                raise ValueError(f"Truth import in {file.name}")
            if isinstance(node, ast.Import) and any(
                "truth" in alias.name.split(".") for alias in node.names
            ):
                raise ValueError(f"Truth import in {file.name}")
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                normalized = node.value.replace("\\", "/")
                if "/sealed/" in normalized or normalized.startswith("sealed/"):
                    raise ValueError(f"Sealed truth path in {file.name}")


def statement_gate(files: Mapping[str, str], statement: str) -> None:
    if not files:
        raise ValueError("No surfaces checked")
    for name, content in files.items():
        if statement not in content:
            raise ValueError(f"Required statement missing in {name}")
