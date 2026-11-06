# ADR-002: Five-Phase Isolated Debate Protocol with Bounded Critique

- **Status**: Accepted
- **Date**: 2026-11-06
- **Deciders**: Project Team (4 Members)

## Context and Problem Statement
When LLM agents see each other's responses from the very first turn, anchoring bias and sycophancy cause subsequent agents to echo the first speaker. Furthermore, open-ended multi-agent loops risk infinite back-and-forth without termination.

## Considered Options
1. **Sequential Round-Robin Open Chat** (Agent 2 sees Agent 1 immediately in Round 1).
2. **Five-Phase Protocol: Frame -> Isolated Propose -> Bounded Critique & Revise -> Converge -> Decide**.
3. **One-Shot Blind Voting without Debate** (Ensemble majority vote without agent-to-agent interaction).

## Decision Outcome
Chosen option: **Option 2 — Five-Phase Isolated Debate Protocol**.

### Consequences & Trade-offs
- **Positive**: Phase 2 (*Propose*) forces each agent to form an independent hypothesis in complete isolation ("think alone, then debate" — Slide 7). Phase 3 (*Critique & Revise*) allows agents to challenge peers and change their minds *only* when presented with superior KB/memory evidence. Bounded rounds (`MAX_CRITIQUE_ROUNDS=2` with early unanimity stop) guarantee deterministic termination.
- **Positive**: Minority views are explicitly captured in the final `ADRDecision.minority_dissent` list rather than erased.

