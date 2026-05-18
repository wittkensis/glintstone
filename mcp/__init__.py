"""Glintstone MCP server — agentic surface for Claude Desktop / Claude Code.

Architecture: the MCP server is a second consumer of the REST API. It calls
the API over httpx; it never reaches into the DB directly. This is the same
two-tier rule the web app follows.

See `.claude/skills/gs-expert-agentic/SKILL.md` for the contract.

Run:
    python -m mcp.server_stdio

Mount in Claude Desktop config:
    {
      "mcpServers": {
        "glintstone": {
          "command": "python3",
          "args": ["-m", "mcp.server_stdio"],
          "cwd": "/path/to/Glintstone/PROJECT",
          "env": {
            "GS_API_URL": "https://api.glintstone.org/api/v2",
            "GS_CLIENT_LABEL": "claude-desktop"
          }
        }
      }
    }
"""

# Merge this package with the installed mcp SDK so that mcp.server.fastmcp
# resolves to the SDK while mcp.client and mcp.server_stdio resolve here.
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
