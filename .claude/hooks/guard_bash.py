#!/usr/bin/env python3
"""PreToolUse hook: block dangerous shell commands before Claude Code runs them.

Claude Code sends the pending tool call as JSON on stdin. Exiting with code 2
blocks the call, and whatever is printed to stderr is shown to Claude as the
reason, so it can pick a safer approach instead of retrying blindly.

Rules live in code, not in CLAUDE.md: a CLAUDE.md rule is a suggestion the
model can forget in a long session, a hook is enforced on every call.
"""
import json
import re
import sys

# (pattern, reason). Patterns are matched against the full command string.
RULES = [
    (r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b\s+(/|~|\$HOME|\*|\.)(\s|$)",
     "recursive force delete of a root, home or current directory"),
    (r"\bgit\s+push\b.*(--force\b|-f\b)(?!-with-lease)",
     "force push; use --force-with-lease and only on your own branch"),
    (r"\bgit\s+reset\s+--hard\b",
     "git reset --hard discards uncommitted work; stash or commit first"),
    (r"\bgit\s+clean\s+-[a-z]*f",
     "git clean -f deletes untracked files permanently"),
    (r"\b(DROP|TRUNCATE)\s+(TABLE|DATABASE)\b",
     "destructive SQL; run it yourself after checking a backup"),
    (r"\bchmod\s+-R\s+777\b",
     "world-writable permissions on a whole tree"),
    (r"(curl|wget)\b[^|]*\|\s*(sudo\s+)?(ba|z)?sh\b",
     "piping a download straight into a shell"),
    (r"\b(cat|less|head|tail|type|more)\b[^|;&]*(\.env\b|id_rsa|\.pem\b|credentials)",
     "printing a secrets file into the transcript"),
]


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # never block on a malformed event

    if event.get("tool_name") != "Bash":
        return 0
    command = (event.get("tool_input") or {}).get("command", "")

    for pattern, reason in RULES:
        if re.search(pattern, command, flags=re.IGNORECASE):
            print(f"Blocked by guard_bash.py: {reason}.\nCommand: {command}",
                  file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
