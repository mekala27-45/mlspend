"""Scan changed text, never print a matched credential or private identifier."""

import re
import subprocess

from packages.core.gates import text_gate
from packages.core.io import ROOT


def scan(files: dict[str, str]) -> None:
    if not files or not any(value.strip() for value in files.values()):
        raise ValueError("Empty diff cannot establish a scan pass")
    private = re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:employee_email|customer_email)\s*[:=]\s*['\"]?[^\s'\"]+@[^\s'\"]+",
        re.I,
    )
    for name, content in files.items():
        if private.search(content):
            raise ValueError("Private key or personal identifier in " + name)
    text_gate(files, check_wording=False)


def main() -> None:
    staged = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    arguments = (
        ["git", "diff", "--cached", "--unified=0"]
        if staged
        else ["git", "diff", "HEAD^", "HEAD", "--unified=0"]
    )
    diff = subprocess.check_output(arguments, cwd=ROOT, text=True, encoding="utf-8")
    files: dict[str, str] = {}
    name = ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            name = line[6:]
        elif (
            line.startswith("+")
            and not line.startswith("+++")
            and name not in {"docs/BUILD_BRIEF.md", "docs/SPEC.md", "tests/test_gates_expanded.py"}
        ):
            files[name] = files.get(name, "") + line[1:] + "\n"
    scan(files)
    print({"diff_files_scanned": len(files), "status": "pass"})


if __name__ == "__main__":
    main()
