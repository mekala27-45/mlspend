from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from packages.core.io import ROOT, STATEMENT, canonical


def render(manifest: dict[str, Any], root: Path = ROOT, check: bool = False) -> None:
    if (
        not manifest.get("monthly")
        or not manifest.get("allocation")
        or manifest.get("statement") != STATEMENT
    ):
        raise ValueError("Manifest is empty or lacks the required statement")
    environment = Environment(
        loader=FileSystemLoader(root / "report/templates"),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    environment.filters["money"] = lambda value: f"${float(value) / 1000000:,.2f}"
    environment.filters["percent"] = lambda value: (
        f"{float(value) * 100:.1f}%" if value is not None else "not measured"
    )
    outputs = {
        "README.md": "readme.md.j2",
        "RESULTS.md": "results.md.j2",
        "report/briefing.md": "briefing.md.j2",
    }
    values = {
        "m": manifest,
        "latest": [r for r in manifest["allocation"] if r["month"] == manifest["latest_month"]],
    }
    for path, template in outputs.items():
        content = environment.get_template(template).render(**values)
        _write_or_check(root / path, content.encode(), check)
    for row in manifest["allocation"]:
        content = environment.get_template("statement.md.j2").render(m=manifest, row=row)
        _write_or_check(
            root / f"report/statements/{row['month']}-{row['team']}.md", content.encode(), check
        )
    for name in ("allocation", "unit", "forecast", "detection", "recommendations", "commitments"):
        content = environment.get_template("method.md.j2").render(m=manifest, name=name)
        _write_or_check(root / f"docs/methods/{name}.md", content.encode(), check)
    _write_or_check(root / "web/data.json", canonical(manifest), check)


def _write_or_check(path: Path, data: bytes, check: bool) -> None:
    if check:
        if not path.exists() or path.read_bytes() != data:
            raise ValueError(f"Generated content drift: {path.name}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
