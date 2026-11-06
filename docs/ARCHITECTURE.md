# Software Architecture Document (SAD)
## AI Assisted Software Architecting Council (2026/27)

- **Course**: Software Architecture 2026/27 — Prof. Henry Muccini, Attilio Di Paolo (Micron), Daniele Spinosi (Micron)
- **Team Members (4)**:
  1. `Studente 1 (Nome Cognome - Matricola)`
  2. `Studente 2 (Nome Cognome - Matricola)`
  3. `Studente 3 (Nome Cognome - Matricola)`
  4. `Studente 4 (Nome Cognome - Matricola)`

---

## 1. Architectural Vision & Context

Architectural decisions are inherently **multi-objective trade-offs** among competing quality attributes (ISO/IEC 25010: Performance Efficiency, Reliability, Security, Maintainability, Operability, Cost). Querying a single Large Language Model (LLM) with a single prompt exhibits **unchallenged confidence bias**: it produces a single viewpoint without peer dissent, often over-engineering solutions (e.g., recommending multi-cluster Kafka or fine-grained Service Mesh microservices to a 3-person ops team).

Our **AI Assisted Software Architecting Council** models a real-world **Architecture Review Board (ARB)** composed of:
1. **Four Swappable Peer Architect Agents**, each powered by a **distinct LLM family** (*Meta Llama 3.3*, *Google Gemini 2.0*, *Alibaba Qwen 3*, *Llama-3.1-Instant / DeepSeek / Mistral*) and assigned a distinct architectural temperament (**Pragmatist**, **Guardian**, **Innovator**, **Skeptic**).
2. **A Chair Architect Agent**, acting as moderator, protocol enforcer, trust-weighted vote aggregator, and author of the final **Architecture Decision Record (ADR)** (explicitly preserving minority dissent).
3. **A Human Architect-in-the-Loop**, who defines requirements, intervenes in the **Short Loop** (live debate revision), and makes the final decision in the **Long Loop** (updating per-model trust weights and organizational principles).

---

## 2. Layered & Component Architecture

```
+-----------------------------------------------------------------------------------+
|                        PRESENTATION & OBSERVABILITY LAYER                         |
|  - Live Council Web UI (HTML5 / CSS3 / JS SPA)                                    |
|  - Real-Time SSE Event Stream Consumer (/api/stream)                              |
|  - 5-Phase Protocol Visualizer, A2A JSON Inspector & Evaluation Lab (Exp A & B)   |
+-----------------------------------------+-----------------------------------------+
                                          | REST + Server-Sent Events (SSE)
+-----------------------------------------v-----------------------------------------+
|                        ORCHESTRATION & DEBATE PROTOCOL LAYER                      |
|  - CouncilOrchestrator (5-Phase Bounded State Machine)                            |
|  - ChairAgent (Context Framer, Trust-Weighted Consensus & Dissent Synthesizer)    |
|  - Peer Architect Pool (Hot-Swappable Registry of ArchitectAgent instances)       |
|  - SingleLLMBaseline Runner (Isolated single-prompt benchmark comparator)         |
+-----------------------------------------+-----------------------------------------+
                                          | Typed A2AMessage & AgentOutputContract
+-----------------------------------------v-----------------------------------------+
|                    COMMUNICATION, GROUNDING & LEARNING LAYER                      |
|  - A2AMessageBus (Observable, Traceable Pub/Sub Bus with Causality Links)         |
|  - KnowledgeBase (Shared RAG over ISO/IEC 25010, Patterns, Tactics & Org ADRs)    |
|  - LongLoopMemory (Episodic Decisions, Learned Principles & Model Trust Weights)  |
+-----------------------------------------+-----------------------------------------+
                                          | Unified Async HTTP JSON Adapter
+-----------------------------------------v-----------------------------------------+
|                         MULTI-LLM PROVIDER ADAPTER LAYER                          |
|  - Groq Cloud API (Llama 3.3 70B, Qwen3 32B, Llama 3.1 8B)                        |
|  - Google Gemini API (Gemini 2.0 Flash)                                           |
|  - OpenRouter / OpenAI / Anthropic Adapters + Deterministic Architectural Sim     |
+-----------------------------------------------------------------------------------+
```

---

## 3. Pillar 1 — The Council: Model Diversity & Stances

All peer agents share the **exact same mandate** (full software architect), the **same shared Knowledge Base**, and the **same typed output contract** (`AgentOutputContract`), while diverging across two orthogonal axes:

| Agent ID | Stance | LLM Family & Default Model | Core Priorities | Architectural Bias |
| :--- | :--- | :--- | :--- | :--- |
| `agent_pragmatist` | **Pragmatist** | Meta Llama (`llama-3.3-70b-versatile`) | Operability, Simplicity, Time-to-Market | Simplest working architecture; protects small ops teams from cognitive overload. |
| `agent_guardian` | **Guardian** | Google Gemini (`gemini-2.0-flash`) | Reliability, Security, Availability, Audit | Risk-averse; prioritizes battle-tested durability, fault isolation, and data sovereignty. |
| `agent_innovator` | **Innovator** | Alibaba Qwen (`qwen/qwen3-32b`) | Scalability, Evolvability, Throughput | Future-proof architectures, cloud-native patterns, and 10x growth headroom. |
| `agent_skeptic` | **Skeptic** | Llama-Instant / Mistral (`llama-3.1-8b-instant`) | Cost (TCO), Maintainability, Fault-Tolerance | Challenges unsubstantiated claims, exposes Day-2 operational taxes, demands KB citations. |
| `agent_chair` | **Chair** | Moderator (`llama-3.3-70b-versatile`) | Consensus, Evidence Quality, Completeness | Frames QA scenarios, computes trust-weighted convergence, records minority dissent in ADR. |

---

## 4. Pillar 2 — Five-Phase Debate Protocol & A2A Communication

To prevent **premature sycophancy** (where LLMs immediately agree with the first speaker), our orchestrator enforces a strict 5-phase protocol:

1. **Phase 1 — FRAME**: The Chair Agent extracts quality attributes and hard constraints, retrieves relevant entries from the shared `KnowledgeBase` and `LongLoopMemory`, and broadcasts a `CONTEXT_FRAME` message on the `A2AMessageBus`.
2. **Phase 2 — PROPOSE (Isolated Thinking)**: Each active `ArchitectAgent` executes `propose_alone()` concurrently/independently **without seeing any peer's output**. Every proposal must adhere to `AgentOutputContract` (selected option, confidence `[0..1]`, trade-off map, and verified KB citation IDs).
3. **Phase 3 — CRITIQUE & REVISE (Bounded Rounds)**: Agents receive the full set of peer proposals from Phase 2. Each agent must challenge conflicting proposals, cite KB evidence (`[KB-PAT-01]`, `[KB-ADR-01]`, `[LEARNED-01]`), and either defend its choice or explicitly flip (`mind_changed = true`) with a documented `change_reason`. Early termination triggers if unanimity is reached.
4. **Phase 4 — CONVERGE**: The Chair computes each option's **Trust-Weighted Consensus Score**:
   $$\text{Score}(o) = \sum_{a \in \text{Agents}(o)} w_{\text{trust}}(a) \cdot \text{conf}(a) \cdot \left(1 + 0.05 \cdot |\text{citations}(a)|\right)$$
   If a deadlock occurs, the Chair breaks ties using organizational principles from `LongLoopMemory`.
5. **Phase 5 — DECIDE**: The Chair generates a structured `ADRDecision` containing the winning option, rationale, synthesized trade-offs, provenance citations, and a dedicated `minority_dissent` array preserving the arguments of any dissenting agents.

### Non-Negotiable Communication Properties (Slide 8)
- **Structured**: Enforced via Pydantic v2 schemas (`A2AMessage`, `AgentOutputContract`, `ADRDecision`).
- **Observable**: Broadcast live over `/api/stream` via Server-Sent Events (SSE) to the web dashboard.
- **Traceable**: Every message records `message_id`, `reply_to_ids`, `sender_id`, `llm_family`, `citations`, and `latency_ms`.
- **Swappable**: Agents are registered in a dynamic configuration pool (`POST /api/agents`) allowing new agents or models to be added at runtime with zero code changes.

---

## 5. Pillar 3 — Grounding & Dual-Loop Feedback Architecture

### 5.1 Shared Knowledge Base with Provenance (`data/knowledge_items.json`)
Contains 18 curated architectural evidence items across 4 categories:
- `KB-ISO-01..04`: **ISO/IEC 25010:2023 Quality Model** (Performance Efficiency, Reliability, Security, Maintainability).
- `KB-PAT-01..08`: **Architectural Pattern Catalog** (NATS JetStream/Redpanda, Kafka+Strimzi, Modular Monolith, Microservices, CQRS/Event Sourcing, Orchestrated vs. Choreographed Saga, TimescaleDB vs. ClickHouse, Edge Store-and-Forward).
- `KB-TAC-01..04`: **Architectural Tactics Catalog** (Transactional Outbox, Bulkhead & Circuit Breaker, Zero-Trust mTLS vs. OIDC Gateway, Strangler Fig + ACL).
- `KB-ADR-01..02`: **Organizational Principles** (Operational Proportionality for Small Teams, Semiconductor Cleanroom Data Sovereignty).

### 5.2 Short Loop & Long Loop Learning (`backend/memory.py`)
- **Short Loop (Intra-Decision)**: The Human Architect submits live critique (`POST /api/debate/short-loop`). The orchestrator injects a `HUMAN_INTERVENTION` message onto the A2A bus and runs an immediate Critique & Revise round so the council updates its ADR proposal before final sign-off.
- **Long Loop (Cross-Decision)**: When the Human Architect commits the final decision (`POST /api/debate/long-loop`):
  1. **Trust Weight Reinforcement**: Agents that voted for the human-approved option receive a trust weight boost ($w_a \leftarrow \min(2.0, w_a + 0.12)$), while diverging agents decay slightly ($w_a \leftarrow \max(0.55, w_a - 0.05)$).
  2. **Principle Extraction**: The human rationale is distilled into a tagged organizational principle (`LEARNED-XX`) stored in `data/memory_store.json` and automatically injected into future debates matching those domain constraints.

