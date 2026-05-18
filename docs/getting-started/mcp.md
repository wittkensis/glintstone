# With Claude (MCP)

Glintstone exposes a Model Context Protocol (MCP) server that connects the corpus to Claude. Same data as the REST API — conversational interface.

## What the MCP server is

The MCP server wraps the Glintstone REST API as four tools. It does not implement any logic itself — it calls the same endpoints the web app uses. Two-tier rule applies: MCP → REST API → PostgreSQL.

Two transports are supported:

- **stdio** — for Claude Desktop and Claude Code CLI (local process)
- **HTTP/SSE** — for Claude.ai web and other HTTP-capable clients

## Prerequisites

Install the MCP SDK into the system Python:

```bash
pip3 install 'mcp[fastmcp]'
```

## Claude Desktop (stdio)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "glintstone": {
      "command": "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
      "args": ["-m", "mcp.server_stdio"],
      "cwd": "/path/to/Glintstone/PROJECT",
      "env": {
        "GS_API_URL": "https://api.glintstone.org/api/v2",
        "GS_CLIENT_LABEL": "claude-desktop"
      }
    }
  }
}
```

Quit Claude Desktop fully (`Cmd+Q`), edit the config, then relaunch. Claude Desktop rewrites the config on exit, so edits made while it is running are lost.

## Claude Code CLI (stdio)

```bash
claude mcp add glintstone \
  -e "GS_API_URL=https://api.glintstone.org/api/v2" \
  -e "GS_CLIENT_LABEL=claude-code" \
  -s user \
  -- \
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -m mcp.server_stdio
```

Then set the working directory in `~/.claude.json` under `mcpServers.glintstone.cwd`.

## Claude.ai web (HTTP/SSE) — not yet implemented

> **Planned.** The HTTP/SSE transport (`mcp.server_http`) is not implemented yet — `mcp/transport/` is empty and the `glintstone-mcp` supervisor service ships with `autostart=false`. Track via issue #83 / `mcp.glintstone.org` work.
>
> Once `mcp.server_http` lands the flow will be:
> ```bash
> python -m mcp.server_http
> ```
> with Claude.ai's MCP connector pointing at `https://mcp.glintstone.org`. See `ops/deploy/` for the service configuration.

## The four tools

**semantic_search** — Search across tablets, lemmas, signs, scholars, publications, named entities, and composites. Uses hybrid lexical + semantic retrieval with Reciprocal Rank Fusion.

**summarize_artifact** — Generate a grounded narrative summary of a single tablet. Lazy-cached: first call generates via Claude, subsequent calls reuse until any cited annotation is superseded.

**interpret_token** — Walk the reading chain for a single token. When lemmatized, returns form → normalized form → lemma → sense with sources. When not lemmatized, returns 1–3 ranked hypotheses with confidence bands.

**submit_correction** — Submit a scholarly correction of something the agent said. Creates a new annotation run and invalidates cached outputs.

## Example

Ask Claude: "Find Ur III tablets mentioning grain distribution."

Claude calls `semantic_search` with `q="grain distribution"` and `types=["tablets"]`. The response includes matching tablets with P-numbers, periods, proveniences, and pipeline stages, plus structured sources for each result.

## Scholarly caveats

MCP hypotheses are phrased as hypotheses. When the pipeline is sparse — no lemmatization, ambiguous sign readings — the tools phrase their output as "resembles," "consistent with," "likely." They do not say "means X" or "is X" for unlemmatized tokens.

Corrections submitted via `submit_correction` are permanent, attributed, and stored in the same trust infrastructure as all other annotation data. They do not overwrite existing records — they layer on top.

## MCP vs API directly

Use the MCP server when you want conversational research with Claude — asking questions, exploring the corpus, following threads. Use the REST API directly when you need programmatic access from your own code, scripted pipelines, or non-Claude clients.
