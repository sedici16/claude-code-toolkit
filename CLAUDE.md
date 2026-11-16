# CLAUDE.md (example)

Keep this file short: it is loaded into context on every turn. Procedures belong
in skills (loaded only when relevant) and hard safety rules belong in hooks
(enforced, not suggested).

## Project
- Python 3.12, FastAPI services, SQLite for app state.
- Run tests with `python -m pytest -q`. Format is handled by the PostToolUse hook.

## Working rules
- Read a file before editing it; prefer small, reviewable diffs.
- Ask before anything outward-facing: deploys, emails, posts, pushes.
- Never print secrets (`.env`, keys) into the conversation. The guard hook blocks
  the obvious cases; don't look for workarounds.
- For long logs, delegate to the `log-investigator` subagent instead of reading them here.
- When reporting, say what was verified and what was not.

## Where things are
- Deploy procedure: skill `deploy-systemd-service`
- Measuring retrieval/answer quality: skill `rag-eval`
- Read-only database access: MCP server `sqlite-readonly`
