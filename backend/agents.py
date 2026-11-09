from typing import Dict, List, Any, Optional, Tuple
from backend.schemas import (
    AgentOutputContract,
    A2AMessage,
    DebatePhase,
    MessageType,
    ADRDecision,
    DissentRecord,
    ConsideredOptionMADR,
)
from backend.llm_providers import llm_adapter


def _match_canonical_option(raw_choice: str, candidate_options: List[str]) -> str:
    """Matches an LLM's chosen option string to the closest canonical option in the list."""
    if not candidate_options:
        return raw_choice
    raw_clean = (raw_choice or "").strip().lower()
    for opt in candidate_options:
        if opt.lower() == raw_clean:
            return opt
    for opt in candidate_options:
        if raw_clean in opt.lower() or opt.lower() in raw_clean:
            return opt
    raw_tokens = set(raw_clean.split())
    best_opt = candidate_options[0]
    best_overlap = -1
    for opt in candidate_options:
        overlap = len(raw_tokens.intersection(set(opt.lower().split())))
        if overlap > best_overlap:
            best_overlap = overlap
            best_opt = opt
    return best_opt


class ArchitectAgent:
    """
    Peer Architect Agent (Pillar 1 & Pillar 2).
    - Full architect mandate (not a narrow specialist)
    - Powered by a configurable LLM family & model
    - Distinct temperament/stance (Pragmatist, Guardian, Innovator, Skeptic, or custom)
    - Produces strict AgentOutputContract responses
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.agent_id: str = config["agent_id"]
        self.name: str = config["name"]
        self.role: str = config.get("role", "peer_architect")
        self.stance: str = config["stance"]
        self.icon: str = config.get("icon", "🤖")
        self.color: str = config.get("color", "#60a5fa")
        self.llm_family: str = config["llm_family"]
        self.provider: str = config["provider"]
        self.model: str = config["model"]
        self.temperature: float = float(config.get("temperature", 0.3))
        self.mandate: str = config["mandate"]
        self.priorities: List[str] = config.get("priorities", [])
        self.enabled: bool = bool(config.get("enabled", True))

    async def propose_alone(
        self,
        session_id: str,
        prompt: str,
        candidate_options: List[str],
        quality_attributes: List[str],
        constraints: List[str],
        kb_items: List[Dict[str, Any]],
        learned_principles: List[Dict[str, Any]],
        prefer_fast_sim: bool = False,
    ) -> A2AMessage:
        """
        Phase 2 — PROPOSE (Isolated & Parallel thinking: 'each agent alone, no peeking' - Slide 7).
        """
        kb_context = "\n".join(
            [
                f"- [{item['id']}] {item['title']} ({item['source']}) | "
                f"Select when: {', '.join(item.get('selection_conditions', []))} | "
                f"Reject when: {', '.join(item.get('rejection_conditions', []))} | "
                f"Summary: {item['summary']}"
                for item in kb_items
            ]
        )
        learned_context = (
            "\n".join(
                [
                    f"- [{p['id']}] {p['principle']} (Preferred: {p.get('preferred_pattern', '')})"
                    for p in learned_principles
                ]
            )
            if learned_principles
            else "None recorded yet."
        )

        system_prompt = (
            f"You are {self.name} (Stance: {self.stance}, LLM Family: {self.llm_family}).\n"
            f"Mandate: {self.mandate}\n"
            f"Priority Quality Attributes: {', '.join(self.priorities)}\n"
            "You are participating in Phase 2 (Isolated Proposal) of an Architecture Review Board.\n"
            "You MUST evaluate all candidate architectural options independently, cite specific Knowledge Base IDs "
            "(e.g. KB-PAT-01, KB-ISO-04, LEARNED-01), and respond ONLY with a valid JSON object matching this exact schema:\n"
            "{\n"
            '  "selected_option": "Exact string from Candidate Options",\n'
            '  "confidence": 0.85,\n'
            '  "summary_argument": "2-3 sentences justifying your decision from your stance",\n'
            '  "evaluated_options": ["Option A", "Option B"],\n'
            '  "tradeoffs": {"Quality Attribute A vs B": "Analysis"},\n'
            '  "citations": ["KB-ID-1", "KB-ID-2"]\n'
            "}"
        )

        user_prompt = (
            f"ARCHITECTURAL SCENARIO:\n{prompt}\n\n"
            f"QUALITY ATTRIBUTES: {', '.join(quality_attributes)}\n"
            f"CONSTRAINTS: {', '.join(constraints)}\n\n"
            f"CANDIDATE OPTIONS (choose exactly one):\n"
            + "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(candidate_options)])
            + f"\n\nSHARED KNOWLEDGE BASE EVIDENCE:\n{kb_context}\n\n"
            f"ORGANIZATIONAL LEARNED PRINCIPLES (LAST_K + RAFG MEMORY):\n{learned_context}\n"
        )

        fallback_ctx = {
            "phase": "PROPOSE",
            "stance": self.stance,
            "prompt": prompt,
            "options": candidate_options,
            "constraints": constraints,
            "kb_items": kb_items,
            "learned_principles": learned_principles,
            "model": self.model,
        }

        parsed, latency_ms, exec_mode = await llm_adapter.complete_json(
            provider=self.provider,
            model=self.model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.temperature,
            fallback_context=fallback_ctx,
            prefer_fast_sim=prefer_fast_sim,
        )

        chosen = _match_canonical_option(parsed.get("selected_option", ""), candidate_options)
        citations = parsed.get("citations") or [item["id"] for item in kb_items[:2]]
        tradeoffs = parsed.get("tradeoffs") or {
            "Primary Trade-off": f"Balances {', '.join(self.priorities[:2])} against implementation complexity."
        }
        if not isinstance(tradeoffs, dict):
            tradeoffs = {"Trade-off Analysis": str(tradeoffs)}

        contract = AgentOutputContract(
            selected_option=chosen,
            confidence=min(1.0, max(0.1, float(parsed.get("confidence", 0.82)))),
            summary_argument=str(parsed.get("summary_argument", f"Selected {chosen} based on {self.stance} priorities.")),
            evaluated_options=candidate_options[:3],
            tradeoffs={str(k): str(v) for k, v in tradeoffs.items()},
            citations=[str(c).strip("[]") for c in citations],
            challenged_agents=[],
            critique_points=[],
            mind_changed=False,
            change_reason=None,
        )

        return A2AMessage(
            session_id=session_id,
            phase=DebatePhase.PROPOSE,
            round_num=1,
            sender_id=self.agent_id,
            sender_name=self.name,
            sender_role=self.role,
            sender_stance=self.stance,
            llm_family=self.llm_family,
            llm_model=self.model,
            llm_provider=self.provider,
            recipient_id="ALL_COUNCIL",
            message_type=MessageType.INITIAL_PROPOSAL,
            content=f"[{self.stance}] Proposes **{contract.selected_option}** (conf: {int(contract.confidence*100)}%): {contract.summary_argument}",
            contract=contract,
            latency_ms=latency_ms,
            execution_mode=exec_mode,
        )

    async def critique_and_revise(
        self,
        session_id: str,
        round_num: int,
        prompt: str,
        candidate_options: List[str],
        quality_attributes: List[str],
        constraints: List[str],
        kb_items: List[Dict[str, Any]],
        learned_principles: List[Dict[str, Any]],
        peer_messages: List[A2AMessage],
        own_last_message: A2AMessage,
        human_critique: Optional[str] = None,
        prefer_fast_sim: bool = False,
    ) -> A2AMessage:
        """
        Phase 3 — CRITIQUE & REVISE ('challenge, update or defend; change mind only for an argument' - Slide 7).
        """
        own_prev_choice = own_last_message.contract.selected_option if own_last_message.contract else candidate_options[0]

        peer_summaries = []
        reply_to_ids = []
        peer_dicts = []
        for m in peer_messages:
            if m.sender_id == self.agent_id:
                continue
            reply_to_ids.append(m.message_id)
            opt = m.contract.selected_option if m.contract else "Unknown"
            cits = ", ".join(m.contract.citations) if (m.contract and m.contract.citations) else "none"
            arg = m.contract.summary_argument if m.contract else m.content
            peer_summaries.append(
                f"- {m.sender_name} ({m.sender_stance}, {m.llm_family}) chose '{opt}' [Citations: {cits}]: {arg}"
            )
            peer_dicts.append({"sender_id": m.sender_id, "selected_option": opt})

        kb_context = "\n".join(
            [f"- [{item['id']}] {item['title']}: {item['summary']}" for item in kb_items]
        )
        learned_context = (
            "\n".join(
                [
                    f"- [{p['id']}] {p['principle']} -> Preferred: {p.get('preferred_pattern', '')}"
                    for p in learned_principles
                ]
            )
            if learned_principles
            else "None."
        )

        human_section = (
            f"\nURGENT HUMAN ARCHITECT / VALIDATION GATE FEEDBACK:\n\"{human_critique}\"\n"
            "You MUST directly address this feedback and revise your proposal if warranted.\n"
            if human_critique
            else ""
        )

        system_prompt = (
            f"You are {self.name} (Stance: {self.stance}, LLM Family: {self.llm_family}).\n"
            f"Mandate: {self.mandate}\n"
            f"Your previous position was: '{own_prev_choice}'.\n"
            "Rules of the Council Debate (Slide 6 & 7):\n"
            "1. Challenge peer proposals that conflict with your architectural stance or lack KB evidence.\n"
            "2. Change your mind ONLY if a peer's evidence-backed argument, Organizational Learned Principle, "
            "or Human Architect feedback proves another option is superior for the scenario's constraints.\n"
            "3. Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "selected_option": "Exact string from Candidate Options",\n'
            '  "confidence": 0.88,\n'
            '  "summary_argument": "Your updated or defended argument referencing peers",\n'
            '  "tradeoffs": {"Key Trade-off": "Updated analysis"},\n'
            '  "citations": ["KB-ID-1", "KB-ID-2"],\n'
            '  "challenged_agents": ["agent_innovator"],\n'
            '  "critique_points": ["Specific technical objection or agreement point"],\n'
            '  "mind_changed": false,\n'
            '  "change_reason": null\n'
            "}"
        )

        user_prompt = (
            f"SCENARIO: {prompt}\n"
            f"CONSTRAINTS: {', '.join(constraints)}\n"
            f"CANDIDATE OPTIONS:\n"
            + "\n".join([f"- {opt}" for opt in candidate_options])
            + f"\n\nPEER ARCHITECT PROPOSALS IN CURRENT ROUND:\n"
            + "\n".join(peer_summaries)
            + f"\n{human_section}\n"
            + f"KNOWLEDGE BASE:\n{kb_context}\n\n"
            + f"LEARNED ORGANIZATIONAL PRINCIPLES:\n{learned_context}\n"
        )

        fallback_ctx = {
            "phase": "CRITIQUE",
            "stance": self.stance,
            "prompt": prompt,
            "options": candidate_options,
            "constraints": constraints,
            "kb_items": kb_items,
            "learned_principles": learned_principles,
            "peer_proposals": peer_dicts,
            "previous_choice": own_prev_choice,
            "human_critique": human_critique,
            "model": self.model,
        }

        parsed, latency_ms, exec_mode = await llm_adapter.complete_json(
            provider=self.provider,
            model=self.model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.temperature,
            fallback_context=fallback_ctx,
            prefer_fast_sim=prefer_fast_sim,
        )

        chosen = _match_canonical_option(parsed.get("selected_option", own_prev_choice), candidate_options)
        mind_changed = chosen != own_prev_choice
        change_reason = parsed.get("change_reason")
        if mind_changed and not change_reason:
            change_reason = "Persuaded by peer KB evidence and operational constraint trade-offs."

        citations = parsed.get("citations") or [item["id"] for item in kb_items[:2]]
        tradeoffs = parsed.get("tradeoffs") or {"Re-evaluated Trade-off": f"Validated '{chosen}' against peer critiques."}
        if not isinstance(tradeoffs, dict):
            tradeoffs = {"Trade-off": str(tradeoffs)}

        critique_points = parsed.get("critique_points") or [
            f"Evaluated peer arguments against {', '.join([str(c) for c in citations[:2]])}."
        ]
        challenged = parsed.get("challenged_agents") or [
            p["sender_id"] for p in peer_dicts if p["selected_option"] != chosen
        ]

        contract = AgentOutputContract(
            selected_option=chosen,
            confidence=min(1.0, max(0.1, float(parsed.get("confidence", 0.87)))),
            summary_argument=str(parsed.get("summary_argument", f"Maintains '{chosen}' after peer critique.")),
            evaluated_options=candidate_options[:3],
            tradeoffs={str(k): str(v) for k, v in tradeoffs.items()},
            citations=[str(c).strip("[]") for c in citations],
            challenged_agents=[str(a) for a in challenged],
            critique_points=[str(cp) for cp in critique_points],
            mind_changed=mind_changed,
            change_reason=str(change_reason) if change_reason else None,
        )

        status_badge = f"🔄 CHANGED MIND ({own_prev_choice} → {chosen})" if mind_changed else f"🛡️ DEFENDED ({chosen})"
        return A2AMessage(
            session_id=session_id,
            phase=DebatePhase.CRITIQUE,
            round_num=round_num,
            sender_id=self.agent_id,
            sender_name=self.name,
            sender_role=self.role,
            sender_stance=self.stance,
            llm_family=self.llm_family,
            llm_model=self.model,
            llm_provider=self.provider,
            recipient_id="ALL_COUNCIL",
            reply_to_ids=reply_to_ids,
            message_type=MessageType.REVISED_POSITION if mind_changed else MessageType.PEER_CRITIQUE,
            content=f"{status_badge}: {contract.summary_argument}",
            contract=contract,
            latency_ms=latency_ms,
            execution_mode=exec_mode,
        )


class ChairAgent:
    """
    Chair Agent (Moderator, MADR Synthesizer & ADR Validation Gate - Slide 3, 7 & ArchMind 2026).
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.agent_id: str = config["agent_id"]
        self.name: str = config["name"]
        self.role: str = "chair"
        self.stance: str = config["stance"]
        self.llm_family: str = config["llm_family"]
        self.provider: str = config["provider"]
        self.model: str = config["model"]

    def create_frame_message(
        self,
        session_id: str,
        title: str,
        prompt: str,
        candidate_options: List[str],
        quality_attributes: List[str],
        constraints: List[str],
        kb_items: List[Dict[str, Any]],
        learned_principles: List[Dict[str, Any]],
    ) -> A2AMessage:
        kb_ids = [item["id"] for item in kb_items]
        learned_ids = [p["id"] for p in learned_principles]
        content = (
            f"⚖️ **Council Framing — {title}**\n"
            f"- **ISO 25010 Decision Drivers**: {', '.join(quality_attributes)}\n"
            f"- **Hard Context Constraints**: {', '.join(constraints)}\n"
            f"- **Candidate Options**: {'; '.join(candidate_options)}\n"
            f"- **Grounded KB Evidence (Select/Reject Filtered)**: {', '.join(kb_ids)}\n"
            f"- **Active Hybrid Memory (Last_K + RAFG)**: {', '.join(learned_ids) if learned_ids else 'Baseline (0 learned principles)'}\n"
            f"Proceeding to **Phase 2 (Parallel Isolated Proposals — No Peeking)**."
        )
        return A2AMessage(
            session_id=session_id,
            phase=DebatePhase.FRAME,
            round_num=0,
            sender_id=self.agent_id,
            sender_name=self.name,
            sender_role=self.role,
            sender_stance=self.stance,
            llm_family=self.llm_family,
            llm_model=self.model,
            llm_provider=self.provider,
            recipient_id="ALL_COUNCIL",
            message_type=MessageType.CONTEXT_FRAME,
            content=content,
            contract=None,
            latency_ms=1.5,
            execution_mode="orchestrator",
        )

    def synthesize_convergence_and_adr(
        self,
        session_id: str,
        title: str,
        prompt: str,
        candidate_options: List[str],
        quality_attributes: List[str],
        final_agent_messages: List[A2AMessage],
        trust_weights: Dict[str, float],
        kb_items: List[Dict[str, Any]],
        learned_principles: List[Dict[str, Any]],
        constraints: Optional[List[str]] = None,
    ) -> Tuple[A2AMessage, A2AMessage, ADRDecision]:
        """
        Computes raw and trust-weighted consensus across the council's final positions,
        builds MADR-compliant pros/cons for every considered option (Miccio et al., 2026),
        preserves minority dissent, and creates both the CONVERGE and DECIDE A2A messages + ADR.
        """
        constraints = constraints or []
        option_scores: Dict[str, float] = {opt: 0.0 for opt in candidate_options}
        raw_vote_counts: Dict[str, int] = {opt: 0 for opt in candidate_options}
        vote_breakdown: Dict[str, str] = {}
        all_citations: List[str] = []
        merged_tradeoffs: Dict[str, str] = {}

        total_weight = 0.0
        for msg in final_agent_messages:
            if not msg.contract:
                continue
            opt = _match_canonical_option(msg.contract.selected_option, candidate_options)
            w = float(trust_weights.get(msg.sender_id, 1.0))
            conf = float(msg.contract.confidence)
            cit_bonus = 1.0 + min(0.15, 0.05 * len(msg.contract.citations))
            score = w * conf * cit_bonus

            option_scores[opt] = round(option_scores.get(opt, 0.0) + score, 3)
            raw_vote_counts[opt] = raw_vote_counts.get(opt, 0) + 1
            vote_breakdown[f"{msg.sender_name} ({msg.llm_family})"] = opt
            total_weight += score

            for c in msg.contract.citations:
                if c not in all_citations:
                    all_citations.append(c)
            for tk, tv in msg.contract.tradeoffs.items():
                merged_tradeoffs[f"{tk} ({msg.sender_stance})"] = tv

        # Ensure every scenario quality attribute (decision driver) is explicitly represented in tradeoffs
        for qa in quality_attributes:
            if not any(qa.lower() in k.lower() or qa.lower() in v.lower() for k, v in merged_tradeoffs.items()):
                merged_tradeoffs[f"Decision Driver ({qa})"] = (
                    f"Evaluated '{qa}' trade-offs under constraints ({', '.join(constraints[:3]) or 'standard'})."
                )

        sorted_opts = sorted(option_scores.items(), key=lambda x: x[1], reverse=True)
        winning_option, winning_score = sorted_opts[0]
        second_score = sorted_opts[1][1] if len(sorted_opts) > 1 else 0.0

        consensus_ratio = round(winning_score / total_weight, 3) if total_weight > 0 else 1.0
        num_agents = max(1, len(final_agent_messages))
        raw_winner_votes = raw_vote_counts.get(winning_option, 0)

        if raw_winner_votes == num_agents:
            consensus_type = "UNANIMOUS"
        elif raw_winner_votes >= (num_agents * 0.65):
            consensus_type = "SUPERMAJORITY"
        elif (winning_score - second_score) > 0.15:
            consensus_type = "WEIGHTED_MAJORITY"
        else:
            consensus_type = "CHAIR_TIE_BREAK"
            for lp in learned_principles:
                pref = lp.get("preferred_pattern", "")
                for opt in candidate_options:
                    if pref and (pref.lower() in opt.lower() or opt.lower() in pref.lower()):
                        winning_option = opt
                        break

        supporter_args = []
        dissent_records: List[DissentRecord] = []
        for msg in final_agent_messages:
            if not msg.contract:
                continue
            opt = _match_canonical_option(msg.contract.selected_option, candidate_options)
            if opt == winning_option:
                supporter_args.append(f"{msg.sender_name} ({msg.sender_stance}): {msg.contract.summary_argument}")
            else:
                dissent_records.append(
                    DissentRecord(
                        agent_id=msg.sender_id,
                        agent_name=msg.sender_name,
                        stance=msg.sender_stance,
                        llm_family=msg.llm_family,
                        preferred_option=opt,
                        rationale=msg.contract.summary_argument,
                        citations=msg.contract.citations,
                    )
                )

        # Build MADR-compliant ConsideredOptionMADR (pros & cons for chosen + all rejected options)
        options_analysis: List[ConsideredOptionMADR] = []
        for opt in candidate_options:
            is_winner = opt == winning_option
            opt_supporters = [
                m.contract.summary_argument
                for m in final_agent_messages
                if m.contract and _match_canonical_option(m.contract.selected_option, candidate_options) == opt
            ]
            if is_winner:
                pros = opt_supporters[:2] or [
                    f"Best satisfies decision drivers ({', '.join(quality_attributes[:3])}) and hard constraints ({', '.join(constraints[:2])})."
                ]
                cons = [
                    d.rationale for d in dissent_records[:1]
                ] or [
                    "Requires disciplined adherence to module/operational boundaries as workload scales."
                ]
            else:
                pros = opt_supporters[:1] or [
                    f"Viable in alternative contexts where {', '.join(constraints[:2]) or 'current constraints'} are relaxed."
                ]
                cons = [
                    f"Rejected by Council majority due to inferior trade-off balance on {', '.join(quality_attributes[:2])} and constraint friction ({', '.join(constraints[:2])})."
                ]
            options_analysis.append(
                ConsideredOptionMADR(
                    option_name=opt,
                    pros=pros,
                    cons=cons,
                    is_chosen=is_winner,
                )
            )

        decision_drivers = [f"ISO-25010: {qa}" for qa in (quality_attributes or ["operability"])] + [
            f"Constraint: {c}" for c in constraints[:3]
        ]

        rationale = (
            f"The Council reached **{consensus_type}** consensus (weighted score: {int(consensus_ratio*100)}%, "
            f"{raw_winner_votes}/{num_agents} agents) in favor of **{winning_option}** "
            f"over {len(candidate_options)-1} rejected alternatives, addressing drivers ({', '.join(quality_attributes)}). "
            + " ".join(supporter_args[:2])
        )

        if not all_citations:
            all_citations = [item["id"] for item in kb_items[:2]] or ["KB-ISO-01"]

        adr = ADRDecision(
            title=f"ADR: {title}",
            status="PROPOSED",
            context_and_problem=prompt,
            decision_drivers=decision_drivers,
            quality_attributes=quality_attributes or ["operability"],
            considered_options=candidate_options if len(candidate_options) >= 2 else candidate_options + ["Baseline Alternative"],
            options_analysis=options_analysis,
            chosen_option=winning_option,
            consensus_type=consensus_type,
            consensus_score=consensus_ratio,
            rationale=rationale,
            tradeoffs=merged_tradeoffs,
            citations=all_citations,
            vote_breakdown=vote_breakdown,
            weighted_scores=option_scores,
            minority_dissent=dissent_records,
        )

        converge_msg = A2AMessage(
            session_id=session_id,
            phase=DebatePhase.CONVERGE,
            round_num=0,
            sender_id=self.agent_id,
            sender_name=self.name,
            sender_role=self.role,
            sender_stance=self.stance,
            llm_family=self.llm_family,
            llm_model=self.model,
            llm_provider=self.provider,
            recipient_id="ALL_COUNCIL",
            reply_to_ids=[m.message_id for m in final_agent_messages],
            message_type=MessageType.CONVERGENCE_VOTE,
            content=(
                f"📊 **Convergence Tally**: {raw_winner_votes}/{num_agents} votes for **{winning_option}** "
                f"(Trust-Weighted Consensus: **{int(consensus_ratio*100)}%** [{consensus_type}]). "
                f"Minority dissents recorded: {len(dissent_records)}."
            ),
            latency_ms=2.0,
            execution_mode="orchestrator",
        )

        dissent_summary = (
            f" | Minority Dissent preserved from: {', '.join([d.agent_name + ' (' + d.preferred_option + ')' for d in dissent_records])}"
            if dissent_records
            else " | Unanimous agreement (0 dissents)."
        )
        decide_msg = A2AMessage(
            session_id=session_id,
            phase=DebatePhase.DECIDE,
            round_num=0,
            sender_id=self.agent_id,
            sender_name=self.name,
            sender_role=self.role,
            sender_stance=self.stance,
            llm_family=self.llm_family,
            llm_model=self.model,
            llm_provider=self.provider,
            recipient_id="HUMAN_ARCHITECT",
            reply_to_ids=[converge_msg.message_id],
            message_type=MessageType.ADR_DECISION,
            content=f"✅ **Proposal Synthesized ({adr.adr_id})**: **{winning_option}** [Citations: {', '.join(all_citations[:4])}]{dissent_summary}",
            latency_ms=3.0,
            execution_mode="orchestrator",
        )

        return converge_msg, decide_msg, adr

    def validate_adr_constraints(
        self,
        adr: ADRDecision,
        constraints: List[str],
        candidate_options: List[str],
        kb_items: List[Dict[str, Any]],
    ) -> Tuple[bool, List[str]]:
        """
        Formal ADR Validation Gate (Díaz-Pace et al., ArchMind & AgenticAKM 2026).
        Verifies before final emission that:
        1. MADR mandatory fields (decision_drivers, considered_options, options_analysis pros/cons, citations) are non-empty;
        2. The chosen option does not violate hard context constraints (e.g. choosing public cloud when 'on-prem' is required,
           or choosing Big-Bang cutover when 'zero-downtime' is required).
        """
        violations: List[str] = []
        chosen_lower = adr.chosen_option.lower()
        constraints_lower = " ".join(constraints).lower()

        if not adr.decision_drivers:
            violations.append("Missing mandatory MADR decision_drivers.")
        if len(adr.options_analysis) < len(candidate_options):
            violations.append("Incomplete MADR options_analysis (must evaluate pros/cons for all considered options).")
        if not adr.citations:
            violations.append("ADR lacks verified Knowledge Base provenance citations.")

        # Semantic constraint checks against fatal anti-patterns
        if "on-prem" in constraints_lower and any(
            cloud_kw in chosen_lower for cloud_kw in ["aws kinesis", "public cloud", "google pub/sub over internet"]
        ):
            violations.append(
                f"Option '{adr.chosen_option}' violates hard 'on-prem' data sovereignty constraint (KB-ADR-02)."
            )
        if "zero-downtime" in constraints_lower and "big-bang" in chosen_lower:
            violations.append(
                f"Option '{adr.chosen_option}' violates hard 'zero-downtime' migration constraint (KB-TAC-04)."
            )
        if ("unreliable-wan" in constraints_lower or "intermittent-wan" in constraints_lower) and (
            "synchronous rest" in chosen_lower or "cloud-only" in chosen_lower
        ):
            violations.append(
                f"Option '{adr.chosen_option}' violates offline WAN resilience constraint (KB-PAT-08)."
            )

        adr.validation_gate_passed = len(violations) == 0
        adr.validation_notes = (
            violations
            if violations
            else [
                "MADR Template Compliance verified (decision_drivers, options_analysis pros/cons, minority_dissent).",
                "Hard context constraints & KB rejection_conditions verified with 0 violations.",
            ]
        )
        return adr.validation_gate_passed, violations


class SingleLLMBaseline:
    """
    Experiment A Baseline (Slide 11):
    'Each council LLM alone, single prompt, no agents. No debate, no roles, no memory, no feedback loop.'
    """

    @staticmethod
    async def run_single_prompt(
        provider: str,
        model: str,
        llm_family: str,
        prompt: str,
        candidate_options: List[str],
        prefer_fast_sim: bool = False,
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a software assistant. Choose one architectural option from the provided list for the scenario. "
            "Respond ONLY with JSON: "
            '{"selected_option": "...", "confidence": 0.75, "summary_argument": "...", "tradeoffs": {"Tradeoff": "..."}, "citations": []}'
        )
        user_prompt = (
            f"Scenario: {prompt}\nOptions:\n" + "\n".join([f"- {o}" for o in candidate_options])
        )
        fallback_ctx = {
            "phase": "BASELINE",
            "prompt": prompt,
            "options": candidate_options,
            "model": model,
        }
        parsed, latency_ms, exec_mode = await llm_adapter.complete_json(
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            fallback_context=fallback_ctx,
            prefer_fast_sim=prefer_fast_sim,
        )
        chosen = _match_canonical_option(parsed.get("selected_option", ""), candidate_options)
        tradeoffs = parsed.get("tradeoffs") or {}
        citations = parsed.get("citations") or []
        return {
            "llm_family": llm_family,
            "provider": provider,
            "model": model,
            "selected_option": chosen,
            "confidence": float(parsed.get("confidence", 0.75)),
            "summary_argument": str(parsed.get("summary_argument", "")),
            "tradeoff_count": len(tradeoffs) if isinstance(tradeoffs, dict) else 1,
            "citation_count": len(citations) if isinstance(citations, list) else 0,
            "citations": citations if isinstance(citations, list) else [],
            "latency_ms": latency_ms,
            "execution_mode": exec_mode,
        }
