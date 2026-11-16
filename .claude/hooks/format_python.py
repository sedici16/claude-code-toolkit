#!/usr/bin/env python3
"""PostToolUse hook: format Python files right after Claude edits them.

Runs `ruff format` (falls back to `black`) on the file that was just written,
so formatting never costs a model turn or a diff review. Silent if neither
formatter is installed, and never blocks: formatting is a convenience.
"""
import json
import shutil
import subprocess
import sys


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    path = (event.get("tool_input") or {}).get("file_path", "")
    if not path.endswith(".py"):
        return 0

    for tool, args in (("ruff", ["format", "--quiet"]), ("black", ["--quiet"])):
        exe = shutil.which(tool)
        if exe:
            subprocess.run([exe, *args, path], check=False, timeout=30)
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
