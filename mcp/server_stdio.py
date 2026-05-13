"""MCP stdio server with the three hero tools.

Run directly:
    python -m mcp.server_stdio

In Claude Desktop config (~/Library/Application Support/Claude/claude_desktop_config.json):

    {
      "mcpServers": {
        "glintstone": {
          "command": "python",
          "args": ["-m", "mcp.server_stdio"],
          "cwd": "/Volumes/Portable Storage/Glintstone",
          "env": {
            "GS_API_URL": "http://api.glintstone.test/api/v2",
            "GS_CLIENT_LABEL": "claude-desktop"
          }
        }
      }
    }

The tools wrap the REST API via httpx — they're not separate implementations.
Same logic, same envelope, same contract. See gs-expert-agentic/SKILL.md.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from mcp.client import GlintstoneAPIClient

logger = logging.getLogger("glintstone.mcp")


def _build_server():
    """Build the FastMCP server. Imports are deferred so the module can be
    inspected without the mcp[fastmcp] package installed."""
    from mcp.server.fastmcp import FastMCP  # type: ignore[import-not-found]

    app = FastMCP(
        name="glintstone",
        instructions=(
            "Glintstone — agentic surface over the cuneiform research corpus. "
            "Use semantic_search for free-text queries across tablets, lemmas, signs, "
            "scholars, and named entities. Use summarize_artifact for a grounded "
            "narrative summary of a tablet (lazy-cached). Use interpret_token for "
            "single-token analysis, including hypotheses when the pipeline is sparse. "
            "Every response includes structured sources for citation."
        ),
    )

    api = GlintstoneAPIClient()

    @app.tool(
        name="semantic_search",
        description=(
            "Search the Glintstone corpus across tablets, lemmas, signs, scholars, "
            "publications, named entities, and composites. Uses hybrid lexical + "
            "semantic retrieval with Reciprocal Rank Fusion. Returns up to 5 results "
            "per entity type with View-All affordances and predictible source attribution."
        ),
    )
    def semantic_search(
        q: str,
        types: list[str] | None = None,
        limit: int = 5,
        mode: str = "hybrid",
    ) -> dict:
        """Search the Glintstone corpus.

        Args:
            q: Free-text query — a phrase, lemma form, P-number, scholar name, etc.
            types: Restrict to these entity types. Omit for all.
                One or more of: tablets, lemmas, signs, scholars, publications, entities, composites.
            limit: Per-group result limit (default 5, max 100).
            mode: Retrieval mode. 'hybrid' (default), 'lexical', or 'semantic'.
        """
        params: dict = {"q": q, "limit": limit, "mode": mode}
        if types:
            params["types"] = types
        return api.get("/search", params=params)

    @app.tool(
        name="summarize_artifact",
        description=(
            "Produce a grounded narrative summary of a single artifact (tablet). "
            "Lazy-cached: first call generates via Claude, subsequent calls reuse "
            "until any cited annotation_run is superseded. For sparse tablets "
            "(pipeline completeness ≤ 2) with similar tablets in the corpus, includes "
            "a phrased-as-hypothesis best-guess section with its own evidence chain. "
            "Every claim cites a source."
        ),
    )
    def summarize_artifact(p_number: str, focus: str = "general") -> dict:
        """Summarize an artifact.

        Args:
            p_number: CDLI P-number, e.g. 'P227657'.
            focus: 'general' | 'research' | 'translation_status'.
        """
        return api.get(f"/artifacts/{p_number}/summary", params={"focus": focus})

    @app.tool(
        name="interpret_token",
        description=(
            "Walk the reading chain for a single token on a tablet. When the chain "
            "is complete (lemmatized), returns form → norm → lemma → sense with sources. "
            "When the token lacks lemmatization, returns 1-3 ranked hypotheses with "
            "confidence bands and evidence chains based on candidate sign readings, "
            "neighbor context, and genre/period priors. Always phrases hypotheses as "
            "'resembles' / 'consistent with' — never 'is X' / 'means X'."
        ),
    )
    def interpret_token(p_number: str, token_id: int) -> dict:
        """Interpret a token.

        Args:
            p_number: CDLI P-number.
            token_id: tokens.id — call other tools or browse first to discover.
        """
        return api.get(f"/artifacts/{p_number}/tokens/{token_id}/interpret")

    @app.tool(
        name="submit_correction",
        description=(
            "Submit a scholarly correction of an agent claim. The correction becomes "
            "a new annotation_run with method='agent-hypothesis-correction', and any "
            "cached agent output that cited the corrected annotation is invalidated."
        ),
    )
    def submit_correction(
        interaction_id: int,
        claim: str,
        correction: str,
        scholar_id: int | None = None,
        evidence: str | None = None,
    ) -> dict:
        """Record a correction. interaction_id is the ToolResponse.interaction_id
        from the response you're correcting."""
        return api.post(
            "/agentic/corrections",
            body={
                "interaction_id": interaction_id,
                "claim": claim,
                "correction": correction,
                "scholar_id": scholar_id,
                "evidence": evidence,
            },
        )

    return app


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    try:
        server = _build_server()
    except ImportError as exc:
        sys.stderr.write(
            f"FastMCP not installed: {exc}\n" "Run: pip install 'mcp[fastmcp]'\n"
        )
        return 1
    # FastMCP exposes both .run() (sync) and async variants depending on version.
    if hasattr(server, "run"):
        server.run()
    else:
        asyncio.run(server.run_stdio())  # type: ignore[attr-defined]
    return 0


if __name__ == "__main__":
    sys.exit(main())
