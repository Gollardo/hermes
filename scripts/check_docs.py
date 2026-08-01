"""Validate local Markdown links and fenced Mermaid blocks."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

LINK_PATTERN = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)")
MERMAID_FENCE = "```mermaid"
EXCLUDED_PARTS = {
    ".angular",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "coverage",
    "dist",
    "node_modules",
}


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*.md") if EXCLUDED_PARTS.isdisjoint(path.parts)
    )


def validate_file(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if content.count("```") % 2:
        errors.append(f"{path}: unbalanced fenced code block")

    for mermaid_section in content.split(MERMAID_FENCE)[1:]:
        diagram = mermaid_section.split("```", maxsplit=1)[0].strip()
        if not diagram.startswith(
            ("flowchart ", "graph ", "sequenceDiagram", "stateDiagram")
        ):
            errors.append(
                f"{path}: Mermaid block has no recognized diagram declaration"
            )

    for target in LINK_PATTERN.findall(content):
        target = target.strip().strip("<>")
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        relative_target = unquote(target.split("#", maxsplit=1)[0])
        if not relative_target:
            continue
        resolved = (path.parent / relative_target).resolve()
        if not resolved.exists():
            errors.append(f"{path}: missing link target {target}")
    return errors


def main() -> int:
    root = Path.cwd()
    errors = [error for path in markdown_files(root) for error in validate_file(path)]
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Markdown links and fences: OK ({len(markdown_files(root))} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
