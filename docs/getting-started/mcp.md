# With Claude (MCP)

Glintstone exposes a Model Context Protocol (MCP) server that connects the corpus to Claude Desktop or Claude Code. Same data as the REST API — conversational interface.

## What the MCP server is

The MCP server is a stdio server that wraps the Glintstone REST API as four tools. It does not implement any logic itself — it calls the same endpoints that the web app uses. Two-tier rule applies: MCP → REST API → PostgreSQL.

## Installation

Install the dependency:

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
        "GS_API_URL": "http://api.glintstone.test/api/v2",
        "GS_CLIENT_LABEL": "claude-desktop"
      }
    }
  }
}
```

For production use, set `GS_API_URL` to `https://api.glintstone.org/api/v2`.

## The four tools

**semantic_search** — Search across tablets, lemmas, signs, scholars, publications, named entities, and composites. Uses hybrid lexical + semantic retrieval with Reciprocal Rank Fusion. Returns up to 5 results per entity type with structured sources.

**summarize_artifact** — Generate a grounded narrative summary of a single tablet. Lazy-cached: the first call is slower (Claude generates it internally), subsequent calls reuse the cached result until any cited annotation is superseded. For sparse tablets, includes a best-guess section phrased as hypotheses.

**interpret_token** — Walk the reading chain for a single token. When lemmatized, returns form → normalized form → lemma → sense with sources. When not lemmatized, returns 1–3 ranked hypotheses with confidence bands and evidence from sign readings, neighbor context, and genre/period priors.

**submit_correction** — Submit a scholarly correction of something the agent said. Creates a new annotation run and invalidates cached outputs.

## Example

Ask Claude: "Find Ur III tablets mentioning grain distribution."

Claude calls `semantic_search` with `q="grain distribution"` and `types=["tablets"]`. The response includes matching tablets with P-numbers, periods, proveniences, and pipeline stages, plus structured sources for each result.

## Scholarly caveats

MCP hypotheses are phrased as hypotheses. When the pipeline is sparse — no lemmatization, ambiguous sign readings — the tools phrase their output as "resembles," "consistent with," "likely." They do not say "means X" or "is X" for unlemmatized tokens.

Corrections submitted via `submit_correction` are permanent, attributed, and stored in the same trust infrastructure as all other annotation data. They do not overwrite existing records — they layer on top.

## MCP vs API directly

Use the MCP server when you want conversational research with Claude — asking questions, exploring corpus, following threads. Use the REST API directly when you need programmatic access from your own code, scripted pipelines, or non-Claude clients.
