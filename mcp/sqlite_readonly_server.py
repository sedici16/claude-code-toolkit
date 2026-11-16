#!/usr/bin/env python3
"""A small read-only SQLite MCP server for Claude Code.

Lets Claude inspect a project database (schema, sample rows, SELECT queries)
without giving it a shell or write access. Useful when the app's state lives
in SQLite and you want answers like "how many listings have no date?" without
Claude writing ad-hoc scripts.

Safety by construction, not by prompt:
- the database is opened with SQLite's read-only URI mode (mode=ro),
- only a single SELECT / WITH statement is accepted,
- results are capped so one query can't flood the context window.

Run:  python mcp/sqlite_readonly_server.py path/to/app.db
"""
import re
import sqlite3
import sys
from pathlib import Path

try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer
except ImportError:  # SDK 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer

MAX_ROWS = 200
MAX_CELL = 300  # characters per cell, long text is truncated

DB_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "app.db").resolve()
mcp = MCPServer("sqlite-readonly")


def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"database not found: {DB_PATH}")
    return sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)


def _fmt(value) -> str:
    s = "NULL" if value is None else str(value)
    return s if len(s) <= MAX_CELL else s[:MAX_CELL] + "…"


@mcp.tool()
def list_tables() -> str:
    """List the tables in the database with their row counts."""
    with _connect() as con:
        names = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        lines = [f"{n}: {con.execute(f'SELECT COUNT(*) FROM \"{n}\"').fetchone()[0]} rows"
                 for n in names]
    return "\n".join(lines) or "(no tables)"


@mcp.tool()
def describe_table(table: str) -> str:
    """Show the columns (name, type, nullability, primary key) of one table."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
        return "Invalid table name."
    with _connect() as con:
        cols = con.execute(f'PRAGMA table_info("{table}")').fetchall()
    if not cols:
        return f"No table named {table}."
    return "\n".join(
        f"{c[1]} {c[2] or 'ANY'}{' NOT NULL' if c[3] else ''}{' PRIMARY KEY' if c[5] else ''}"
        for c in cols)


@mcp.tool()
def query(sql: str, limit: int = 50) -> str:
    """Run one read-only SELECT (or WITH ... SELECT) and return the rows as a table.

    Results are capped at `limit` rows (max 200).
    """
    statement = sql.strip().rstrip(";")
    if ";" in statement:
        return "Only a single statement is allowed."
    if not re.match(r"(?is)^\s*(select|with)\b", statement):
        return "Only SELECT / WITH queries are allowed."
    limit = max(1, min(int(limit), MAX_ROWS))
    try:
        with _connect() as con:
            cur = con.execute(statement)
            headers = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(limit + 1)
    except sqlite3.Error as e:
        return f"SQLite error: {e}"
    more = len(rows) > limit
    rows = rows[:limit]
    out = [" | ".join(headers), " | ".join("---" for _ in headers)]
    out += [" | ".join(_fmt(v) for v in r) for r in rows]
    if more:
        out.append(f"(truncated at {limit} rows; refine the query or raise limit)")
    return "\n".join(out)


if __name__ == "__main__":
    mcp.run()
