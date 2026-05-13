"""Agent services — the core/agent package powers the agentic surface.

See `.claude/skills/gs-expert-agentic/SKILL.md` for the architecture.

Modules:
  voyage_client     — Voyage embeddings (voyage-3-large) with batch + hash-skip
  anthropic_client  — Claude wrapper with prompt caching baked in
  citation_parser   — Parse [n] markers from synthesis output; validate
  synthesis         — Grounded synthesis loop (assemble facts → call Claude → validate)
  search_engine     — Hybrid lexical + semantic search with RRF fusion
  fact_assembly     — assemble_facts() for summarize / interpret
  agent_outputs     — Lazy persist + supersession invalidation
  interactions      — agent_interactions logging middleware helper
"""
