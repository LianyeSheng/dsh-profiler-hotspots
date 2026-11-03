#!/usr/bin/env python3
"""Repository-wide link and anchor verification entry point."""

from __future__ import annotations

import argparse
import os
import sys

from document_links import validate_links
from document_sources import document_sources, find_root


def unchecked_items():
    print("\nNot automatically checked (review required)")
    print("  J4 Whether a code anchor is needed; checklist: .agents/se/contracts/anchor-convention.md")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify repository-root links and code anchors")
    parser.add_argument(
        "--base",
        default=os.environ.get("RFC_COMPARE_BASE"),
        help="Explicit nonzero, resolvable CI comparison-base SHA",
    )
    parser.add_argument(
        "--staged", action="store_true", help="Check the actual index snapshot against HEAD"
    )
    parser.add_argument("--quiet-warnings", action="store_true", help="Hide non-blocking warnings")
    try:
        args = parser.parse_args(argv)
        with document_sources(find_root(), base=args.base, staged=args.staged) as sources:
            findings, scanned = validate_links(sources.root, sources.changed)
            for finding in findings:
                if finding.severity == "error" or not args.quiet_warnings:
                    print(finding.render(sources.root) + "\n")
            errors = sum(finding.severity == "error" for finding in findings)
            warnings = len(findings) - errors
            print(
                f"verify-links: {'passed' if not errors else 'failed'} "
                f"({scanned} files, {errors} errors, {warnings} warnings)"
            )
            return 1 if errors else 0
    except (ValueError, UnicodeError, OSError) as exc:
        print(f"verify-links: {exc}", file=sys.stderr)
        return 2
    finally:
        unchecked_items()


if __name__ == "__main__":
    sys.exit(main())
