---
name: gs-expert-agentic
description: Glintstone's agentic surface — MCP + REST in unison, grounded synthesis with citations, lazy-persist agent outputs, and the learning loop. Use for any work on mcp/, core/schemas/envelope.py, core/schemas/citation.py, core/agent/, agent_interactions/agent_outputs migrations, or the debug UI.
metadata:
  question: "How is the agentic surface (MCP + REST) wired, how do grounded summaries cite sources, and how does the system learn from every interaction?"
  created: 2026-05-12
  modified: 2026-05-12
  context: "Created during the agentic-architecture planning thread (2026-05-12). Owns the Pydantic-first contract that keeps MCP and REST aligned, the ToolResponse envelope, the own-rolled citation contract, the three hero scenarios, and the agent learning loop."
  status: active
  audience: [claude, engineers]
  owners: [eric]
  related_issues: ["#25", "#50", "#55", "#56"]
  related_skills: [gs-orient-project, gs-expert-data-model, gs-expert-deployment, gs-curator-docs]
  supersedes: null
  superseded_by: null
  triggers: [mcp, agentic, agent, semantic search, embedding, voyage, pgvector, "summarize_artifact", "interpret_token", "semantic_search", citation, grounded, synthesis, "ToolResponse", envelope, "agent_outputs", "agent_interactions", debug ui, "core/agent", "core/schemas"]
---

# Glintstone agentic surface

The MCP server, the REST endpoints, and the grounded-synthesis pipeline are **one system seen from three angles**. They share Pydantic models, the response envelope, the citation contract, and the learning loop. This skill is the contract.

## North-star scenarios

Three scenarios drive every architectural decision. If a change makes any of them worse, push back.

| # | Scenario | Hero tool | Latency budget |
|---|---|---|---|
| 1 | **Semantic Search** — phrase → artifacts, scholars, studies, lemmas, glosses, signs | `semantic_search` | < 800 ms incl. query embedding |
| 2 | **Artifact Summary** — what this tablet is, how well understood, research relevance, best-guess if poorly understood | `summarize_artifact` | < 3 s first call, < 200 ms reused |
| 3 | **Token Interpretation** — selected token without a translation pipeline → grounded hypothesis | `interpret_token` | < 3 s first call, < 200 ms reused |

Detail: [hero-tools.md](hero-tools.md).

## When to load which file

| Question | File |
|---|---|
| "What shape does a tool response take? What's a `render_hint`? How does View-All work?" | [envelope.md](envelope.md) |
| "How does grounded synthesis cite sources? What's the reject-retry rule?" | [citation-contract.md](citation-contract.md) |
| "What do `semantic_search` / `summarize_artifact` / `interpret_token` accept and return? What are the litmus tests?" | [hero-tools.md](hero-tools.md) |
| "How do `agent_interactions`, `interaction_feedback`, `agent_outputs` work? When are summaries invalidated?" | [learning-loop.md](learning-loop.md) |
| "What architectural decisions are locked, when, and why?" | [decisions.md](decisions.md) |
| "What's the exact prompt sent to Claude for summarize_artifact / interpret_token?" | [prompts/](prompts/) |

## Non-negotiables

- **Pydantic-first.** Every request and response shape lives in `core/schemas/`. FastAPI and FastMCP both import from there. The OpenAPI YAML at `data-model/glintstone-schema-api.yaml` is generated, not hand-edited.
- **Every tool response uses `ToolResponse`.** Same envelope, every surface. Same `sources[]` field on every response, never empty.
- **Lazy persist, never pre-bake.** `summarize_artifact` and `interpret_token` outputs are generated on first request and cached in `agent_outputs` until superseded by a newer annotation_run.
- **No claim without a citation.** The synthesis validator rejects any LLM output containing claims without `[n]` markers bound to the provided source list. One retry, then fail.
- **Required attributions surfaced.** When an eBL or ORACC source contributed, `required_attributions` is populated and non-strippable.
- **MCP ⇄ REST parity.** Every REST route that's user-facing has a matching MCP tool. Enforced by `tests/contract/test_api_mcp_parity.py`.

## Architecture in one diagram

```
                        Client (Claude Desktop / Claude Code / browser)
                              │
              ┌───────────────┴───────────────┐
              │                               │
        MCP server (stdio)            FastAPI api/ (REST)
              │                               │
              └─────────────► httpx ◄─────────┘
                              │
                core/agent/   (search_engine, synthesis, citation_parser)
                core/schemas/ (envelope, citation, sources, search, agent)
                              │
                       Postgres (pgvector + tsvector + pg_trgm)
                              │
              ┌───────────────┼───────────────────────────┐
              │               │                           │
       relational core    entity_embeddings        agent_interactions
                                                    interaction_feedback
                                                    agent_outputs
```

The MCP server doesn't reach into the DB. It calls REST. Same pattern as the web app — same two-tier rule applied a second time. This is what makes API ⇄ MCP alignment a runtime guarantee, not a convention.

## Freshness contract this skill owns

- `core/schemas/envelope.py` → [envelope.md](envelope.md)
- `core/schemas/citation.py` → [citation-contract.md](citation-contract.md)
- `core/agent/*.py` → [hero-tools.md](hero-tools.md)
- Any migration touching `agent_*` tables → [learning-loop.md](learning-loop.md)
- Files under `prompts/` → bump filename `vN.md` on any change that breaks the citation contract; bump frontmatter `revision:` on minor tweaks.

Enforced by `gs-curator-docs`. Any commit touching the above must touch the matching skill file in the same commit.

## Deeper reading

- [docs/agent-surface.md](../../../docs/agent-surface.md) — generated from this skill + Pydantic schemas; the public-facing version
- Issue [#25](https://github.com/wittkensis/glintstone/issues/25) — Global Semantic Search PRD (closes naturally as scenario 1 stabilizes)
- Issue [#55](https://github.com/wittkensis/glintstone/issues/55) / [#56](https://github.com/wittkensis/glintstone/issues/56) — Knowledge Bar PRDs that consume `summarize_artifact` and `interpret_token`
