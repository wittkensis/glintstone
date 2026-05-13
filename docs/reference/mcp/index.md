# MCP Reference

The Glintstone MCP server exposes the corpus to Claude as four tools. It is a stdio server — Claude Desktop or Claude Code launches it as a subprocess and communicates over stdin/stdout.

## Architecture

```
Claude (Desktop or Code)
  |
  | MCP stdio protocol
  |
mcp/server_stdio.py
  |
  | httpx (HTTP)
  |
REST API (api.glintstone.org)
  |
  | psycopg
  |
PostgreSQL
```

The MCP server is a thin wrapper. It calls the same REST endpoints the web app uses. No separate logic, no separate data. Two-tier rule applies throughout.

## Installation

```bash
pip install 'mcp[fastmcp]'
```

## Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "glintstone": {
      "command": "python",
      "args": ["-m", "mcp.server_stdio"],
      "cwd": "/path/to/Glintstone",
      "env": {
        "GS_API_URL": "https://api.glintstone.org/api/v2",
        "GS_CLIENT_LABEL": "claude-desktop"
      }
    }
  }
}
```

## The four tools

| Tool | Description |
|------|-------------|
| [semantic_search](/docs/reference/mcp/semantic-search/) | Search across tablets, lemmas, signs, scholars, publications, entities, composites |
| [summarize_artifact](/docs/reference/mcp/summarize-artifact/) | Grounded narrative summary of a single tablet, lazy-cached |
| [interpret_token](/docs/reference/mcp/interpret-token/) | Reading chain when lemmatized; ranked hypotheses when not |
| [submit_correction](/docs/reference/mcp/submit-correction/) | Record a scholarly correction — flows into annotation_runs |

## When to use MCP vs the API directly

**Use MCP** when you want conversational research with Claude: exploring the corpus by asking questions, following a train of thought across artifact types, requesting summaries or interpretations in prose.

**Use the REST API directly** when you need programmatic access from your own code, scripted ETL pipelines, or non-Claude clients. The API has finer-grained control over pagination, filtering, and response shape.

Both surfaces expose the same underlying data. The MCP tools are structured to be useful to Claude in a research context; the REST API is structured to be useful to code.
