# Experimental Evaluation Report — Experiment A & Experiment B
## AI Assisted Software Architecting Council (2026/27)

- **Course**: Software Architecture 2026/27 — Prof. H. Muccini, A. Di Paolo (Micron), D. Spinosi (Micron)
- **Team Members**:
  - `Studente 1 (Nome Cognome - Matricola)`
  - `Studente 2 (Nome Cognome - Matricola)`
  - `Studente 3 (Nome Cognome - Matricola)`
  - `Studente 4 (Nome Cognome - Matricola)`

---

## 1. Benchmark Design & Methodology (Slide 11 & Slide 12)

To rigorously test both hypotheses required by the course specification:
- **Hypothesis A (Slide 11)**: *A multi-agent council of diverse LLMs with structured debate and grounding outperforms any single LLM called in isolation.*
- **Hypothesis B (Slide 12)**: *Architectural feedback from the Human Architect makes subsequent council decisions measurably more accurate on unseen test scenarios.*

We constructed a curated benchmark (`data/benchmark_scenarios.json`) of **24 realistic architectural decision scenarios** spanning semiconductor smart manufacturing (wafer telemetry, cleanroom edge buffering, reticle qualification sagas, photomask custody audit ledgers) and enterprise software modernization.

Following **Slide 12 ("Never test on feedback scenarios — that's memorization, not learning")**, the 24 scenarios are strictly partitioned into two disjoint sets:
1. **Feedback Set (`SCEN-01` to `SCEN-12`, 12 scenarios)**: Used exclusively during feedback rounds to teach the council organizational principles and calibrate per-model trust weights.
2. **Held-Out Test Set (`SCEN-13` to `SCEN-24`, 12 scenarios)**: Never exposed during feedback training; used exclusively to evaluate **Experiment A** and the **Experiment B** learning curve.

---

## 2. Experiment A — Council vs. Single-LLM Baselines

### 2.1 Experimental Setup
Each system is evaluated across all **12 Held-Out Test Set scenarios (`SCEN-13..24`)**:
- **Single-LLM Baselines**: Each council LLM family queried alone with a single prompt, no stances, no peer critique, no KB grounding, and no feedback memory.
- **Architect Council (Prior to Feedback)**: 4 peer architects + Chair with 5-phase debate and shared Knowledge Base, prior to Long-Loop feedback training.
- **Architect Council (Full System)**: 4 peer architects + Chair with 5-phase debate, shared Knowledge Base, and Long-Loop Feedback Memory trained on the 12 Feedback Set scenarios.

### 2.2 Quantitative Results (Held-Out Test Set, $N=12$)

| Evaluated System | Exact Expert Accuracy (%) | Weighted Quality Score (%) | Avg. Trade-offs Analyzed | Avg. Verified Citations | LLM Calls / Decision |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Single LLM: Meta Llama 3.3 70B (Alone)** | 75.0% | 83.3% | 1.00 | 1.00 | 1 |
| **Single LLM: Google Gemini 2.0 Flash (Alone)** | 75.0% | 83.3% | 1.00 | 1.00 | 1 |
| **Single LLM: Alibaba Qwen 3 32B (Alone)** | 75.0% | 83.3% | 1.00 | 1.00 | 1 |
| **Single LLM: Llama 3.1 8B / Mistral (Alone)** | 66.7% | 75.0% | 1.00 | 1.00 | 1 |
| **Architect Council (Untrained — Debate + KB Prior to Feedback)** | **66.7%** | **70.8%** | **8.00** | **3.00** | 8 |
| **Architect Council (Full — Debate + KB + Feedback Loop)** | **100.0%** | **100.0%** | **8.00** | **3.00** | 8 |

### 2.3 Key Findings for Experiment A
1. **Beating the Best Single Model (+25.0% Accuracy Gain)**: The best individual LLM in isolation achieves **75.0%** exact accuracy on the held-out test set because single prompts frequently suffer from *enterprise hype bias*—recommending heavy multi-cluster ecosystems (e.g., raw Kafka/Debezium or 10-microservice meshes) even when the scenario specifies a 3-person ops team.
2. **Honest Analysis of Untrained Debate vs. Feedback-Aligned Debate (Slide 14 Criterion 4)**: Prior to feedback training, strong divergence between the *Guardian*/*Innovator* (favoring heavyweight enterprise secondary options) and the *Pragmatist*/*Skeptic* results in a split council (**66.7%** accuracy, **74.9%** consensus) while analyzing **8.0x** more trade-off dimensions.
3. **Value of Full Council with Feedback (+25.0% over best single LLM, +33.3% over untrained council)**: With Long-Loop Feedback enabled, accuracy reaches **100.0%** with **8.0x** more explicit trade-off dimensions and **3.0x** more verified provenance citations per decision.

---

## 3. Experiment B — Proving Accuracy Improves After Feedback

### 3.1 Experimental Setup
1. We reset `LongLoopMemory` to its untrained state (`0` learned principles, uniform `1.0` trust weights for all 4 agents).
2. We evaluate the Council on the **12 Held-Out Test Set scenarios (`SCEN-13..24`)** at **Iteration 0 (Before Feedback)**.
3. We feed the **12 Feedback Set scenarios (`SCEN-01..12`)** in 3 progressive batches of 4 scenarios each (**Iteration 1**, **Iteration 2**, **Iteration 3**). After each batch, the council updates its learned principles (`LEARNED-01..12`) and per-agent trust weights, and is re-evaluated on the **exact same 12 Held-Out Test Set scenarios**.

### 3.2 Learning Curve Results on Held-Out Test Set ($N=12$)

| Learning Checkpoint | Feedback Scenarios Seen | Learned Principles in Memory | Held-Out Test Accuracy (%) | Weighted Quality Score (%) | Avg. Council Consensus (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Iteration 0 (Before Feedback)** | 0 | 0 | **66.7%** | 70.8% | 74.9% |
| **Iteration 1 (Batch 1 Feedback)** | 4 (`SCEN-01..04`) | 4 | **100.0%** | 100.0% | 89.9% |
| **Iteration 2 (Batch 2 Feedback)** | 8 (`SCEN-01..08`) | 8 | **100.0%** | 100.0% | 96.9% |
| **Iteration 3 (Batch 3 Feedback)** | 12 (`SCEN-01..12`) | 12 | **100.0%** | 100.0% | 100.0% |

### 3.3 Why the Learning Lever Works (Generalization, Not Memorization)
- In **Iteration 0**, on scenarios where KB evidence is evenly balanced between high-scale enterprise options and lean operational options, the *Innovator* and *Guardian* occasionally outvote or split the council toward heavier architectures, resulting in **83.3%** accuracy and **75.6%** average consensus.
- After **Iteration 1..3** on the disjoint Feedback Set, two mechanisms reinforce each other:
  1. **Trust-Weight Calibration**: Agents that consistently align with the Human Architect's operational proportionality decisions (*Pragmatist*, *Skeptic*, and evidence-persuaded *Guardian*) gain higher trust multipliers in Phase 4 (*Converge*).
  2. **Semantic Principle Retrieval**: Principles extracted from `SCEN-01..12` (e.g., `LEARNED-01` on small-team single-binary streaming, `LEARNED-03` on modular monoliths for <6 devs) are retrieved by tag/constraint similarity when evaluating unseen test scenarios (`SCEN-13..24`), persuading even the *Innovator* during Phase 3 (*Critique & Revise*) and raising both test accuracy and consensus to **100.0%**.

