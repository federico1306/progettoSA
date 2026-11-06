# ADR-004: Shared RAG Knowledge Base with Explicit Citation Provenance

- **Status**: Accepted
- **Date**: 2026-11-06
- **Deciders**: Project Team (4 Members)

## Context and Problem Statement
Architectural arguments without citations degrade into generic LLM opinions (Slide 9). We need a grounding mechanism that gives all council LLMs fair access to the same authoritative sources (ISO/IEC 25010, architectural patterns, tactics, and organizational principles) and tracks provenance.

## Considered Options
1. **Shared Structured JSON Knowledge Base with Tag/Quality-Attribute Retrieval & Citation ID Enforcement (`KB-ISO-*`, `KB-PAT-*`, `KB-TAC-*`, `KB-ADR-*`)**.
2. **Per-Agent Private Knowledge Silos**.
3. **Ungrounded LLM Parametric Memory Only**.

## Decision Outcome
Chosen option: **Option 1 — Shared Structured Knowledge Base with Explicit Citation Provenance**.

### Consequences & Trade-offs
- **Positive**: All peer architects receive the exact same retrieved evidence pack during Phase 1 (*Frame*), ensuring a fair debate across different LLM families.
- **Positive**: Every `AgentOutputContract` and synthesized `ADRDecision` contains machine-verifiable citation IDs (e.g., `[KB-PAT-01]`, `[KB-ADR-01]`) that resolve directly to source metadata in the UI.

