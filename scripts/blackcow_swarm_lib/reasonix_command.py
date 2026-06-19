from __future__ import annotations

from typing import Final

# Reasonix ACP loads user-configured MCP servers before session/new unless a
# CLI MCP override is present. An empty override keeps swarm worker startup local
# and deterministic.
ACP_MCP_ISOLATION_ARGS: Final[tuple[str, str]] = ("--mcp", "")
ACP_MODEL_PREFLIGHT_PROMPT: Final[str] = (
    "BlackCow Reasonix model connectivity preflight. "
    "Reply with OK only. Do not inspect files, run tools, or use repository context."
)
