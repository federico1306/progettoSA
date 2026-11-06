# ADR-001: Multi-LLM Council Composition and Orthogonal Architect Stances

- **Status**: Accepted
- **Date**: 2026-11-06
- **Deciders**: Project Team (4 Members)

## Context and Problem Statement
A single LLM call suffers from model-specific inductive bias and confident hallucination of over-engineered architectures. However, simply running multiple instances of the same LLM (or different LLMs with identical neutral prompts) still leads to rapid, shallow convergence because instruction-tuned LLMs are trained to be agreeable. How should we structure the agent pool to guarantee genuine trade-off exploration while keeping the comparison fair?

## Considered Options
1. **Specialist Role Decomposition** (e.g., Database Agent, Security Agent, Network Agent) on a single LLM.
2. **Peer Architects across >=3 Distinct LLM Families with Orthogonal Stances** (Pragmatist, Guardian, Innovator, Skeptic) + Neutral Chair Agent.
3. **Unstructured Free-Form Chat among 4 Identical Prompts**.

## Decision Outcome
Chosen option: **Option 2 — Peer Architects across Distinct LLM Families with Orthogonal Stances + Chair Agent**.

### Consequences & Trade-offs
- **Positive**: Every agent holds a full software architect mandate and accesses the exact same Knowledge Base, ensuring a fair debate (Slide 5). Combining model diversity (Meta Llama, Google Gemini, Alibaba Qwen, Llama-Instant/Mistral) with explicit temperaments (*Pragmatist*, *Guardian*, *Innovator*, *Skeptic*) guarantees initial divergence on competing ISO/IEC 25010 quality attributes.
- **Negative**: Higher token usage and latency compared to a single LLM prompt (mitigated by bounded critique rounds and async execution).

