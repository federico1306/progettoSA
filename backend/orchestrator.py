import copy
import time
import uuid
from typing import Dict, List, Any, Optional
from backend.config import DEFAULT_AGENT_POOL, CHAIR_AGENT_CONFIG, settings
from backend.schemas import (
    DebateSession,
    StartDebateRequest,
    ShortLoopFeedbackRequest,
    LongLoopDecisionRequest,
    A2AMessage,
    DebatePhase,
    MessageType,
    AgentConfigModel,
)
from backend.agents import ArchitectAgent, ChairAgent
from backend.bus import message_bus
from backend.knowledge_base import knowledge_base
from backend.memory import long_loop_memory


class CouncilOrchestrator:
    """
    Orchestrates the 5-Phase Debate Protocol (Slide 7):
    Frame -> Propose (Isolated) -> Critique & Revise (Bounded) -> Converge -> Decide (ADR + Dissent)
    Plus Pillar 3 Short-Loop and Long-Loop Human Architect Feedback (Slide 10).
    """

    def __init__(self) -> None:
        self._agent_configs: List[Dict[str, Any]] = copy.deepcopy(DEFAULT_AGENT_POOL)
        self.chair = ChairAgent(CHAIR_AGENT_CONFIG)
        self.sessions: Dict[str, DebateSession] = {}
        # Map of latest agent message per session for short-loop continuation
        self._latest_agent_messages: Dict[str, Dict[str, A2AMessage]] = {}

    def get_agent_pool(self) -> List[Dict[str, Any]]:
        trust = long_loop_memory.get_trust_weights()
        enriched = []
        for cfg in self._agent_configs:
            item = dict(cfg)
            item["trust_weight"] = trust.get(cfg["agent_id"], 1.0)
            enriched.append(item)
        return enriched

    def get_active_agents(self) -> List[ArchitectAgent]:
        return [ArchitectAgent(cfg) for cfg in self._agent_configs if cfg.get("enabled", True)]

    def add_or_update_agent(self, agent_cfg: AgentConfigModel) -> List[Dict[str, Any]]:
        """Hot-swaps or adds a peer architect agent without code rewrites (Slide 8)."""
        data = agent_cfg.model_dump()
        data["role"] = "peer_architect"
        for idx, existing in enumerate(self._agent_configs):
            if existing["agent_id"] == data["agent_id"]:
                self._agent_configs[idx] = data
                break
        else:
            self._agent_configs.append(data)
        return self.get_agent_pool()

    def toggle_agent(self, agent_id: str, enabled: bool) -> List[Dict[str, Any]]:
        for cfg in self._agent_configs:
            if cfg["agent_id"] == agent_id:
                cfg["enabled"] = enabled
        return self.get_agent_pool()

    def remove_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        self._agent_configs = [c for c in self._agent_configs if c["agent_id"] != agent_id]
        return self.get_agent_pool()

    def reset_agent_pool(self) -> List[Dict[str, Any]]:
        self._agent_configs = copy.deepcopy(DEFAULT_AGENT_POOL)
        return self.get_agent_pool()

    async def run_debate(
        self,
        req: StartDebateRequest,
        prefer_fast_sim: bool = False,
    ) -> DebateSession:
        t_start = time.perf_counter()
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        title = req.title or "Architectural Decision Scenario"
        quality_attributes = req.quality_attributes or ["latency", "operability", "reliability", "scalability"]
        constraints = req.constraints or ["production-grade", "small-ops-team"]
        candidate_options = req.candidate_options or [
            "NATS JetStream (Clustered Go Single-Binary) or Redpanda",
            "Apache Kafka on Kubernetes with Strimzi Operator (KRaft mode)",
            "Modular Monolith with Explicit Domain Boundaries & Single PostgreSQL",
            "Domain-Aligned Microservices with API Gateway & Service Mesh",
        ]

        # Grounding: Retrieve shared KB items & Long-Loop learned principles
        kb_items = knowledge_base.retrieve(
            query=f"{title} {req.requirements_prompt}",
            quality_attributes=quality_attributes,
            constraints=constraints,
            top_k=5,
        )
        learned_principles = (
            long_loop_memory.retrieve_relevant_principles(
                prompt=f"{title} {req.requirements_prompt}",
                quality_attributes=quality_attributes,
                constraints=constraints,
                top_k=4,
            )
            if req.use_long_loop_memory
            else []
        )

        session = DebateSession(
            session_id=session_id,
            scenario_id=req.scenario_id,
            title=title,
            requirements_prompt=req.requirements_prompt,
            candidate_options=candidate_options,
            quality_attributes=quality_attributes,
            constraints=constraints,
            retrieved_kb_items=kb_items,
            applied_learned_principles=learned_principles,
        )
        self.sessions[session_id] = session

        # ---------------------------------------------------------------------
        # PHASE 1: FRAME (Chair sets context & QA scenarios)
        # ---------------------------------------------------------------------
        await message_bus.publish_status(session_id, "FRAME", "Chair Agent framing context & grounding KB...")
        frame_msg = self.chair.create_frame_message(
            session_id=session_id,
            title=title,
            prompt=req.requirements_prompt,
            candidate_options=candidate_options,
            quality_attributes=quality_attributes,
            constraints=constraints,
            kb_items=kb_items,
            learned_principles=learned_principles,
        )
        await message_bus.publish(frame_msg)
        session.messages.append(frame_msg)

        # ---------------------------------------------------------------------
        # PHASE 2: PROPOSE (Each agent alone, no peeking)
        # ---------------------------------------------------------------------
        await message_bus.publish_status(
            session_id, "PROPOSE", "Peer Architects formulating independent proposals in isolation..."
        )
        active_agents = self.get_active_agents()
        latest_by_agent: Dict[str, A2AMessage] = {}

        for agent in active_agents:
            prop_msg = await agent.propose_alone(
                session_id=session_id,
                prompt=req.requirements_prompt,
                candidate_options=candidate_options,
                quality_attributes=quality_attributes,
                constraints=constraints,
                kb_items=kb_items,
                learned_principles=learned_principles,
                prefer_fast_sim=prefer_fast_sim,
            )
            await message_bus.publish(prop_msg)
            session.messages.append(prop_msg)
            latest_by_agent[agent.agent_id] = prop_msg

        # ---------------------------------------------------------------------
        # PHASE 3: CRITIQUE & REVISE (Bounded rounds)
        # ---------------------------------------------------------------------
        max_rounds = max(1, min(3, req.max_critique_rounds))
        for r in range(1, max_rounds + 1):
            await message_bus.publish_status(
                session_id,
                "CRITIQUE",
                f"Critique & Revise Round {r}/{max_rounds}: Agents challenging peers and testing evidence...",
            )
            current_round_peers = list(latest_by_agent.values())
            new_latest: Dict[str, A2AMessage] = {}
            for agent in active_agents:
                crit_msg = await agent.critique_and_revise(
                    session_id=session_id,
                    round_num=r,
                    prompt=req.requirements_prompt,
                    candidate_options=candidate_options,
                    quality_attributes=quality_attributes,
                    constraints=constraints,
                    kb_items=kb_items,
                    learned_principles=learned_principles,
                    peer_messages=current_round_peers,
                    own_last_message=latest_by_agent[agent.agent_id],
                    human_critique=None,
                    prefer_fast_sim=prefer_fast_sim,
                )
                await message_bus.publish(crit_msg)
                session.messages.append(crit_msg)
                new_latest[agent.agent_id] = crit_msg
            latest_by_agent = new_latest

            # Early termination if unanimous agreement is reached after at least 1 critique round
            distinct_choices = {
                m.contract.selected_option for m in latest_by_agent.values() if m.contract
            }
            if len(distinct_choices) == 1:
                break

        self._latest_agent_messages[session_id] = latest_by_agent

        # ---------------------------------------------------------------------
        # PHASE 4 & 5: CONVERGE & DECIDE (Chair tallies votes, records dissent, writes ADR)
        # ---------------------------------------------------------------------
        await message_bus.publish_status(
            session_id, "CONVERGE", "Chair Agent computing trust-weighted consensus & minority dissent..."
        )
        trust_weights = (
            long_loop_memory.get_trust_weights()
            if req.use_long_loop_memory
            else {a.agent_id: 1.0 for a in active_agents}
        )
        converge_msg, decide_msg, adr = self.chair.synthesize_convergence_and_adr(
            session_id=session_id,
            title=title,
            prompt=req.requirements_prompt,
            candidate_options=candidate_options,
            quality_attributes=quality_attributes,
            final_agent_messages=list(latest_by_agent.values()),
            trust_weights=trust_weights,
            kb_items=kb_items,
            learned_principles=learned_principles,
        )
        await message_bus.publish(converge_msg)
        session.messages.append(converge_msg)

        await message_bus.publish_status(session_id, "DECIDE", "ADR synthesized and ready for Human Architect review.")
        await message_bus.publish(decide_msg)
        session.messages.append(decide_msg)

        session.adr = adr
        session.total_latency_ms = round((time.perf_counter() - t_start) * 1000.0, 1)
        return session

    async def apply_short_loop_feedback(
        self,
        req: ShortLoopFeedbackRequest,
        prefer_fast_sim: bool = False,
    ) -> DebateSession:
        """
        Pillar 3 — Short Loop (Slide 10):
        Human Architect provides feedback on the current proposal; the council runs an immediate
        revision round and synthesizes an updated ADR.
        """
        session = self.sessions.get(req.session_id)
        if not session:
            raise ValueError(f"Session {req.session_id} not found")

        session.short_loop_iterations += 1
        if req.new_constraint and req.new_constraint not in session.constraints:
            session.constraints.append(req.new_constraint)
        for qa in req.emphasized_quality_attributes:
            if qa not in session.quality_attributes:
                session.quality_attributes.append(qa)

        human_msg = A2AMessage(
            session_id=session.session_id,
            phase=DebatePhase.HUMAN_FEEDBACK,
            round_num=session.short_loop_iterations,
            sender_id="human_architect",
            sender_name="Human Architect",
            sender_role="human_architect",
            sender_stance="Decision Maker",
            llm_family="Human-in-the-Loop",
            llm_model="Human Architect",
            llm_provider="human",
            recipient_id="ALL_COUNCIL",
            message_type=MessageType.HUMAN_INTERVENTION,
            content=f"👨‍💻 **Human Architect Short-Loop Review**: \"{req.human_critique}\"",
            latency_ms=0.0,
            execution_mode="human",
        )
        await message_bus.publish(human_msg)
        session.messages.append(human_msg)

        active_agents = self.get_active_agents()
        latest_by_agent = self._latest_agent_messages.get(session.session_id, {})
        current_peers = list(latest_by_agent.values())
        new_latest: Dict[str, A2AMessage] = {}

        for agent in active_agents:
            own_prev = latest_by_agent.get(agent.agent_id) or session.messages[1]
            rev_msg = await agent.critique_and_revise(
                session_id=session.session_id,
                round_num=10 + session.short_loop_iterations,
                prompt=session.requirements_prompt,
                candidate_options=session.candidate_options,
                quality_attributes=session.quality_attributes,
                constraints=session.constraints,
                kb_items=session.retrieved_kb_items,
                learned_principles=session.applied_learned_principles,
                peer_messages=current_peers,
                own_last_message=own_prev,
                human_critique=req.human_critique,
                prefer_fast_sim=prefer_fast_sim,
            )
            await message_bus.publish(rev_msg)
            session.messages.append(rev_msg)
            new_latest[agent.agent_id] = rev_msg

        self._latest_agent_messages[session.session_id] = new_latest
        trust_weights = long_loop_memory.get_trust_weights()
        converge_msg, decide_msg, updated_adr = self.chair.synthesize_convergence_and_adr(
            session_id=session.session_id,
            title=f"{session.title} (Revised #{session.short_loop_iterations})",
            prompt=session.requirements_prompt,
            candidate_options=session.candidate_options,
            quality_attributes=session.quality_attributes,
            final_agent_messages=list(new_latest.values()),
            trust_weights=trust_weights,
            kb_items=session.retrieved_kb_items,
            learned_principles=session.applied_learned_principles,
        )
        await message_bus.publish(converge_msg)
        session.messages.append(converge_msg)
        await message_bus.publish(decide_msg)
        session.messages.append(decide_msg)
        session.adr = updated_adr
        return session

    def apply_long_loop_decision(self, req: LongLoopDecisionRequest) -> Dict[str, Any]:
        """
        Pillar 3 — Long Loop (Slide 10):
        Stores the final Human Architect decision, updates per-model trust weights,
        and extracts reusable organizational principles for all future debates.
        """
        session = self.sessions.get(req.session_id)
        if not session or not session.adr:
            raise ValueError(f"Session {req.session_id} or ADR not found")

        latest_by_agent = self._latest_agent_messages.get(req.session_id, {})
        agent_votes = {
            aid: (msg.contract.selected_option if msg.contract else "")
            for aid, msg in latest_by_agent.items()
        }

        session.adr.status = "ACCEPTED"
        session.adr.human_approved = (
            session.adr.chosen_option.strip().lower() == req.final_chosen_option.strip().lower()
        )
        session.adr.human_final_decision = req.final_chosen_option
        session.adr.human_notes = req.human_rationale

        learning_update = long_loop_memory.record_human_decision(
            session_id=session.session_id,
            scenario_title=session.title,
            requirements_prompt=session.requirements_prompt,
            final_chosen_option=req.final_chosen_option,
            human_rationale=req.human_rationale,
            agent_votes=agent_votes,
            extracted_principle=req.extracted_principle,
            trigger_tags=req.trigger_tags or session.constraints + session.quality_attributes,
        )

        return {
            "session_id": session.session_id,
            "adr": session.adr.model_dump(),
            "learning_update": learning_update,
        }


orchestrator = CouncilOrchestrator()

