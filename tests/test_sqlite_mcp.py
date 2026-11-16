"""End-to-end test of the MCP server: start it over stdio and call its tools with the MCP client."""
import asyncio
import subprocess
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "mcp" / "sqlite_readonly_server.py"
DB = ROOT / "examples" / "demo.db"


def setup_module():
    subprocess.run([sys.executable, str(ROOT / "examples" / "make_demo_db.py")], check=True)


async def _call(tool: str, args: dict) -> str:
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER), str(DB)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, args)
            return "".join(c.text for c in result.content if hasattr(c, "text"))


def call(tool: str, args: dict | None = None) -> str:
    return asyncio.run(_call(tool, args or {}))


def test_list_tables():
    out = call("list_tables")
    assert "nights: 3 rows" in out and "venues: 3 rows" in out


def test_describe_table():
    assert "signup TEXT NOT NULL" in call("describe_table", {"table": "nights"})


def test_select_query():
    out = call("query", {"sql": "SELECT name FROM venues WHERE city = 'Pisa'"})
    assert "Circolo" in out


def test_rejects_writes():
    assert "Only SELECT" in call("query", {"sql": "DELETE FROM venues"})
    assert "single statement" in call("query", {"sql": "SELECT 1; DROP TABLE venues"})
    # the table is still there
    assert "venues: 3 rows" in call("list_tables")


def test_readonly_even_through_with():
    out = call("query", {"sql": "WITH x AS (SELECT 1) INSERT INTO venues(name, city) VALUES ('x','y')"})
    assert "SQLite error" in out or "Only SELECT" in out
    assert "venues: 3 rows" in call("list_tables")
