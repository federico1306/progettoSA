# ADR-003: Typed, Observable, and Swappable A2A Message Bus

- **Status**: Accepted
- **Date**: 2026-11-06
- **Deciders**: Project Team (4 Members)

## Context and Problem Statement
Slide 8 mandates four non-negotiable communication requirements: **Structured** (typed message schema), **Observable** (visible live in the demo), **Traceable** (who said what, based on what), and **Swappable** (add an agent without rewrites). Heavyweight external frameworks often obscure raw prompts and make live UI streaming brittle.

## Considered Options
1. **Custom Lightweight Async Pub/Sub Event Bus (`A2AMessageBus`) with Pydantic v2 Schemas & Server-Sent Events (SSE)**.
2. **External Message Broker (RabbitMQ / Redis PubSub) + Complex Multi-Process Workers**.
3. **Opaque Framework Internal Callbacks (Black-Box Agent Chain)**.

## Decision Outcome
Chosen option: **Option 1 — Custom Lightweight Async Pub/Sub Event Bus with Pydantic v2 Contracts & SSE**.

### Consequences & Trade-offs
- **Positive**: Zero external infrastructure dependencies (`setup < 2 min`). Every message is strictly validated against `A2AMessage` and `AgentOutputContract`, preserving full causality (`reply_to_ids`, `citations`, `challenged_agents`, `mind_changed`).
- **Positive**: Real-time SSE streaming (`/api/stream`) pushes every agent thought and state transition directly to the browser UI as it happens.
- **Positive**: Dynamic agent registry (`POST /api/agents`) enables hot-swapping or adding a 5th/6th agent at runtime without modifying orchestrator code.

