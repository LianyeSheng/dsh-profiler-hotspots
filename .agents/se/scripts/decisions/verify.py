#!/usr/bin/env python3
"""Global RFC document verification entry point."""

from __future__ import annotations

import argparse
import os
import sys

from document_sources import document_sources, find_root
from document_validation import validate_documents


def unchecked_items():
    print("\nNot automatically checked (review required)")
    print(
        "  J1 When to write a record   J2 One record = one constraint   J3 Whether alternatives are genuine"
    )
    print("  Checklist: .agents/se/contracts/review-checklist.md")
    print(
        "  Evidence semantics, translation fidelity, substantive resolution, reviewer confirmation, and human approval are not automatically established."
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify RFC records, evidence chains and marked examples"
    )
    parser.add_argument(
        "--base",
        default=os.environ.get("RFC_COMPARE_BASE"),
        help="Explicit nonzero, resolvable CI comparison-base SHA",
    )
    parser.add_argument(
        "--staged", action="store_true", help="Check the actual index snapshot against HEAD"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Only fix status lines that require no judgment"
    )
    parser.add_argument("--quiet-warnings", action="store_true", help="Hide non-blocking warnings")
    try:
        args = parser.parse_args(argv)
        with document_sources(
            find_root(),
            base=args.base,
            staged=args.staged,
            fix=args.fix,
        ) as sources:
            report = validate_documents(sources, fix=args.fix)
            for finding in report.findings:
                if finding.severity == "error" or not args.quiet_warnings:
                    print(finding.render(report.root) + "\n")
            if report.overview:
                print("RFC evidence overview (author assessments; no approval inferred):")
                for row in report.overview:
                    print("  " + row)
                print(
                    f"  localized unresolved={sum('author-resolution=unresolved' in r for r in report.overview)}; unresolved-blocking={sum('blocking=yes' in r and 'author-resolution=unresolved' in r for r in report.overview)}; unverified={len(report.overview)}"
                )
            errors = sum(f.severity == "error" for f in report.findings)
            warnings = len(report.findings) - errors
            print(
                f"rfc-workflow: {'passed' if report.exit_code == 0 else 'failed'} ({report.records} records, {errors} errors, {warnings} warnings)"
            )
            return report.exit_code
    except (ValueError, UnicodeError, OSError) as exc:
        print(f"rfc-workflow: [X1/E3] {exc}", file=sys.stderr)
        return 2
    finally:
        unchecked_items()


if __name__ == "__main__":
    sys.exit(main())
