# AI Assisted Software Architecting Council (2026/27)

> **Course Project — Software Architecture 2026/27**  
> **Professors & Mentors**: Prof. Henry Muccini &bull; Attilio Di Paolo (Micron) &bull; Daniele Spinosi (Micron)  
> **Team Members (4)**:
> - `Studente 1 (Nome Cognome - Matricola)`
> - `Studente 2 (Nome Cognome - Matricola)`
> - `Studente 3 (Nome Cognome - Matricola)`
> - `Studente 4 (Nome Cognome - Matricola)`

---

## Overview & Three Core Pillars

This repository implements an **AI Assisted Software Architecture Review Board (Architect Council)** where peer AI architects—each powered by a **distinct LLM family** and holding a **distinct architectural temperament (Stance)**—independently propose solutions, debate and challenge each other using a grounded Knowledge Base, and converge on a formal **Architecture Decision Record (ADR)** while preserving minority dissent.

### 1. Pillar 1 — Diverse & Swappable Council (`backend/config.py`, `backend/agents.py`)
- **4 Peer Architect Agents + 1 Chair Agent** across distinct LLM families:
  - ⚙️ **Pragmatist Architect** (*Meta Llama 3.3 70B* via Groq) — Values operational simplicity, rapid time-to-market, and team cognitive load limits.
  - 🛡️ **Guardian Architect** (*Google Gemini 2.0 Flash* via Gemini API) — Risk-averse; prioritizes reliability, security, data sovereignty, and battle-tested durability.
  - 🚀 **Innovator Architect** (*Alibaba Qwen 3 32B* via Groq) — Champions future-proof scalability, high throughput, and modern cloud-native patterns.
  - 🧐 **Skeptic Architect** (*Llama 3.1 8B Instant / Mistral / DeepSeek*) — Challenges unsubstantiated claims, exposes Day-2 operational costs, and demands KB evidence.
  - ⚖️ **Chair Architect** (*Moderator & Synthesizer*) — Frames context, computes trust-weighted consensus, breaks deadlocks, and writes the final ADR with minority dissent.
- **Hot-Swappable at Runtime**: Add a 5th agent or swap any model/stance live from the UI (**Tab 2**) or via `POST /api/agents` without touching a single line of code.

### 2. Pillar 2 — Five-Phase Debate Protocol & Observable A2A Bus (`backend/orchestrator.py`, `backend/bus.py`)
- **5-Phase Bounded Protocol**:
  1. `FRAME`: Chair sets quality attribute scenarios, constraints, and retrieves shared KB & Long-Loop Memory.
  2. `PROPOSE (Isolated)`: Each peer architect forms its initial proposal **alone (no peeking)** using a strict `AgentOutputContract` JSON schema.
  3. `CRITIQUE & REVISE (Bounded)`: Agents inspect peers' proposals, challenge conflicting claims with KB citations, and either defend their choice or explicitly flip (`mind_changed=true` + `change_reason`).
  4. `CONVERGE`: Chair computes trust-weighted consensus scores and resolves deadlocks.
  5. `DECIDE`: Chair synthesizes a formal `ADRDecision` explicitly recording `minority_dissent`.
- **Real-Time Observability**: Every `A2AMessage` is streamed live over Server-Sent Events (`/api/stream`) to the Web UI.

### 3. Pillar 3 — Grounding & Dual-Loop Feedback (`backend/knowledge_base.py`, `backend/memory.py`)
- **Shared Knowledge Base (`data/knowledge_items.json`)**: 18 authoritative items covering **ISO/IEC 25010:2023**, **Architectural Patterns**, **Architectural Tactics**, and **Organizational ADRs** with strict citation provenance (`[KB-ISO-01]`, `[KB-PAT-01]`, `[KB-ADR-01]`).
- **Short Loop (Intra-Decision)**: Human Architect submits live review feedback during a session (`POST /api/debate/short-loop`), triggering an immediate council revision round.
- **Long Loop (Cross-Decision)**: Human Architect commits the final decision (`POST /api/debate/long-loop`), which updates **per-agent trust weights** and extracts reusable **Organizational Learned Principles (`LEARNED-XX`)** that measurably improve accuracy on future decisions.

---

## Quick Start (< 2 Minutes Setup)

### Prerequisites
- **Python 3.10+** (tested with Python 3.13)

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure API Keys (`.env`)
Copy `.env.example` to `.env` (already configured in this workspace) and set your keys (`GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, etc.).  
*Note*: The system also includes a built-in deterministic **Context-Aware Architectural Simulator** fallback (`LLM_MODE=auto` / `fast_sim`), so the Live Demo and Evaluation Suite run out-of-the-box even offline or under API rate limits.

### 3. Run the Live Demo Server
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Or simply double-click / run `.\start.bat`.  
Then open **http://127.0.0.1:8000** in your browser!

### 4. Run Automated Tests & Evaluation Suite
```powershell
pytest -v
```

---

## Six Deliverables Mapping (Slide 13)

| # | Deliverable | Location in Repository |
| :---: | :--- | :--- |
| **1** | **Working Council + Baseline** | `backend/` (`orchestrator.py`, `agents.py`, `bus.py`, `llm_providers.py`) |
| **2** | **Architecture Document** | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (also viewable in Web UI Tab 5) |
| **3** | **ADRs (5 Design Decisions)** | [`docs/adr/`](docs/adr/) (`ADR-001` through `ADR-005`, also viewable in Web UI Tab 5) |
| **4** | **Evaluation Report (Exp A & B)** | [`docs/EVALUATION_REPORT.md`](docs/EVALUATION_REPORT.md) + Interactive Runner in Web UI Tab 4 |
| **5** | **Clean Source Repo (<10 min setup)** | `README.md`, `requirements.txt`, `.env.example`, `start.bat`, `tests/test_council.py` |
| **6** | **Live Demo UI** | `frontend/` (`index.html`, `styles.css`, `app.js`) served at `http://127.0.0.1:8000` |

