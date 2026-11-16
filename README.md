# claude-code-toolkit

A small, working set of [Claude Code](https://docs.claude.com/en/docs/claude-code) extensions
taken from my day-to-day setup: hooks, an MCP server, skills and a subagent.
Everything here is tested (`pytest`, 23 tests) and meant to be copied into a real project.

The idea behind the layout: **keep CLAUDE.md short, move procedures into skills,
and enforce safety rules in hooks.** A rule in CLAUDE.md is a suggestion that can be
forgotten in a long session; a hook runs on every tool call. Skills are only loaded
when relevant, so they don't cost context on every turn.

```
.claude/
  settings.json                  # wires the hooks + deny rules for secrets
  hooks/guard_bash.py            # PreToolUse: blocks dangerous shell commands
  hooks/format_python.py         # PostToolUse: ruff/black on edited .py files
  skills/deploy-systemd-service/ # deploy a FastAPI app behind a Cloudflare Tunnel
  skills/rag-eval/               # measure RAG/search changes with before/after numbers
  agents/log-investigator.md     # subagent: reads big logs, returns only root cause
mcp/sqlite_readonly_server.py    # MCP server: read-only SQLite access for Claude
.mcp.json                        # registers the MCP server for this project
CLAUDE.md                        # example of a short project memory file
tests/                           # hook tests + end-to-end MCP tests over stdio
```

## Hooks

**`guard_bash.py`** (PreToolUse, matcher `Bash`) reads the pending tool call from stdin and
exits with code 2 to block it. The reason goes to stderr, so Claude sees *why* and picks a
safer route instead of retrying. It blocks recursive deletes of `/`, `~` or `.`, `git push --force`
(but allows `--force-with-lease`), `git reset --hard`, `git clean -f`, `DROP/TRUNCATE`,
`chmod -R 777`, `curl | sh`, and printing secrets files (`.env`, private keys) into the transcript.

**`format_python.py`** (PostToolUse, matcher `Edit|Write`) formats the file Claude just wrote,
so formatting never costs a model turn. It never blocks.

## MCP server: `sqlite-readonly`

Gives Claude three tools on a project database, without a shell or write access:
`list_tables`, `describe_table`, `query` (a single `SELECT`/`WITH`, results capped at 200 rows
and long cells truncated so one query can't flood the context window).

Read-only is enforced by SQLite itself (`mode=ro` URI), not by the prompt: even a
`WITH … INSERT` fails. Works with the MCP Python SDK 1.x and 2.x.

## Skills

- **`deploy-systemd-service`**: step-by-step deploy of a Python web app as a systemd *user*
  service bound to `127.0.0.1`, exposed only through a Cloudflare Tunnel, with a backup of
  the tunnel config, ingress validation and a health check before reporting success.
- **`rag-eval`**: a fixed test set, hit@1/hit@5, answer checks, refusals and cost per question;
  change one thing at a time and report before/after on the same set. It also gives an
  order for diagnosing a wrong answer: retrieval → ranking → generation → missing content.

## Subagent: `log-investigator`

Runs on a small model with read-only tools, finds the *first* error in large logs and replies
in at most 15 lines. The point is context hygiene: thousands of log lines stay in the
subagent's context, the main session only gets the root cause and the evidence.

## Try it

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Linux/macOS: .venv/bin/pip
.venv/Scripts/python examples/make_demo_db.py
.venv/Scripts/python -m pytest -q               # 23 passed
claude                                          # approve the project MCP server when asked
```

`.mcp.json` runs the server with `python`; point it at the venv's interpreter (or install
`mcp` globally) so the server can import the SDK.

## License

MIT
