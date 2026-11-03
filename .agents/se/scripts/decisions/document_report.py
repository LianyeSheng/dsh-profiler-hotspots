"""A single gate finding with the executable four-part report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CONTRACT_REL = ".agents/se/contracts/note-format.md"


@dataclass
class Finding:
    rule: str
    path: Path
    line: int | None
    found: str
    expect: str
    fix: str
    severity: str = "error"
    contract: str = CONTRACT_REL

    def render(self, root: Path) -> str:
        mark = "✗" if self.severity == "error" else "⚠"
        loc = str(self.path.relative_to(root))
        if self.line is not None:
            loc = f"{loc}:{self.line}"
        return (
            f"{mark} {loc}  [{self.rule}]\n"
            f"  Found: {self.found}\n"
            f"  Expected: {self.expect}\n"
            f"  Fix: {self.fix}\n"
            f"  Contract: {self.contract}#{self.rule.lower()}"
        )
