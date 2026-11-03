#!/usr/bin/env python3
"""Reject secret environment files anywhere in the Git index, even if unchanged."""
from pathlib import PurePosixPath
import subprocess
import sys


def forbidden(path):
    name = PurePosixPath(path).name
    return name == ".env" or (name.startswith(".env.") and name != ".env.example")


def main():
    result = subprocess.run(
        ["git", "ls-files", "--cached", "-z"], capture_output=True, check=True)
    paths = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    blocked = sorted(set(path for path in paths if path and forbidden(path)))
    if blocked:
        print("Commit blocked: secret environment files are present in the Git index:",
              file=sys.stderr)
        for path in blocked:
            print(f"  {path!r}", file=sys.stderr)
        print("Remove them from the index with git rm --cached -- <path>; keep local files.",
              file=sys.stderr)
        unchecked()
        return 1
    unchecked()
    return 0


def unchecked():
    print("Unchecked: secret contents under other filenames, past commits, and disabled checks.",
          file=sys.stderr)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, subprocess.CalledProcessError):
        unchecked()
        sys.exit("Cannot inspect Git index; refusing to continue.")
