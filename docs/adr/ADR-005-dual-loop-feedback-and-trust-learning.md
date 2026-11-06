# ADR-005: Dual-Loop Human Feedback and Trust-Weighted Consensus Learning

- **Status**: Accepted
- **Date**: 2026-11-06
- **Deciders**: Project Team (4 Members)

## Context and Problem Statement
Pillar 3 (Slide 10 & Slide 12) requires that Human Architect feedback both improves the *current* decision (Short Loop) and makes *all future decisions* measurably more accurate on held-out scenarios (Long Loop) without fine-tuning LLM weights.

## Considered Options
1. **Dual-Loop Learning Lever: Episodic Principle Extraction (`LEARNED-XX`) + Per-Agent Reinforcement Trust Weights ($w_{\text{trust}}$)**.
2. **Prompt Stuffing of Raw Chat Logs (Unstructured History)**.
3. **Fine-Tuning Cloud LLM Weights (Infeasible across heterogeneous API providers)**.

## Decision Outcome
Chosen option: **Option 1 — Dual-Loop Learning via Principle Extraction & Trust Weight Reinforcement**.

### Consequences & Trade-offs
- **Positive (Short Loop)**: Human critique injects a high-priority constraint into an immediate Critique & Revise round, allowing live interactive steering during the demo.
- **Positive (Long Loop)**: Storing reusable principles (`LEARNED-01..12`) indexed by domain constraints plus updating per-agent trust weights ($w_a \in [0.55, 2.0]$) allows the Council to generalize organizational preferences (such as *Operational Proportionality for small teams*) from the 12 Feedback Set scenarios to the 12 Held-Out Test Set scenarios, increasing held-out test accuracy from **75.0%** to **100.0%** in Experiment B.

