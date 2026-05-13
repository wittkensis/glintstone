"""Contract test: REST routes under /search and /agent have matching MCP tools.

This is the load-bearing test for the API ⇄ MCP alignment principle. When
adding a new agentic route, register the corresponding MCP tool in the same
PR or this test fails.

Both sides are parsed from source rather than imported so the test runs
without FastAPI / FastMCP installed.
"""

import pathlib
import re
from typing import Set


_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

# REST routes that are part of the agentic surface (i.e. should have MCP twins)
_EXPECTED_PAIRS = [
    # (rest_route_path_template, mcp_tool_name)
    ("/search", "semantic_search"),
    ("/artifacts/{p_number}/summary", "summarize_artifact"),
    ("/artifacts/{p_number}/tokens/{token_id}/interpret", "interpret_token"),
    ("/agentic/corrections", "submit_correction"),
]


def _rest_paths_from_source() -> Set[str]:
    """Read api/routes/search.py and api/routes/agent.py; pull out the prefix
    and route paths via regex."""
    paths: set[str] = set()
    for relpath in ("api/routes/search.py", "api/routes/agent.py"):
        text = (_PROJECT_ROOT / relpath).read_text(encoding="utf-8")
        # APIRouter(prefix="/agentic", ...) → capture each router's prefix
        # and bind it to subsequent @router.{get,post,...}("...") decorators.
        # Simple two-pass: find every (router_name, prefix) and every
        # (router_name, path) in source order.
        router_prefixes: dict[str, str] = {}
        for match in re.finditer(
            r"(\w+)\s*=\s*APIRouter\((.*?)\)", text, flags=re.DOTALL
        ):
            name, args = match.group(1), match.group(2)
            prefix_match = re.search(r'prefix\s*=\s*"([^"]*)"', args)
            router_prefixes[name] = prefix_match.group(1) if prefix_match else ""
        for match in re.finditer(
            r'@(\w+)\.(?:get|post|put|delete|patch)\(\s*"([^"]+)"', text
        ):
            router_name, path = match.group(1), match.group(2)
            prefix = router_prefixes.get(router_name, "")
            paths.add(prefix + path)
    return paths


def _mcp_tool_names_in_source() -> Set[str]:
    """Read gs_mcp/server_stdio.py and pull out @app.tool(name="...") declarations.

    Read as source rather than executing, since FastMCP may not be installed
    in CI."""
    src_path = _PROJECT_ROOT / "gs_mcp" / "server_stdio.py"
    text = src_path.read_text(encoding="utf-8")
    return set(re.findall(r'@app\.tool\(\s*name\s*=\s*"([^"]+)"', text))


def test_every_expected_pair_has_both_sides():
    rest_paths = _rest_paths_from_source()
    mcp_tools = _mcp_tool_names_in_source()

    missing_rest: list[str] = []
    missing_mcp: list[str] = []

    for path, tool in _EXPECTED_PAIRS:
        if path not in rest_paths:
            missing_rest.append(path)
        if tool not in mcp_tools:
            missing_mcp.append(tool)

    failures: list[str] = []
    if missing_rest:
        failures.append(f"REST routes missing: {missing_rest}")
    if missing_mcp:
        failures.append(f"MCP tools missing: {missing_mcp}")
    assert not failures, "\n".join(failures)


def test_no_unexpected_mcp_tools():
    """If we add a new MCP tool, we expect a REST route too — flag drift early."""
    mcp_tools = _mcp_tool_names_in_source()
    expected = {tool for _, tool in _EXPECTED_PAIRS}
    extra = mcp_tools - expected
    assert not extra, (
        f"MCP tools registered without a matching expected REST route: {extra}. "
        f"Add the route to _EXPECTED_PAIRS in this test (and add a REST endpoint)."
    )
