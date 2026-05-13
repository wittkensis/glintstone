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
          "command": "python",
          "args": ["-m", "mcp.server_stdio"],
          "env": {
            "GS_API_URL": "http://api.glintstone.test/api/v2",
            "GS_CLIENT_LABEL": "claude-desktop"
          }
        }
      }
    }
"""
