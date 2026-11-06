from typing import Dict, List, Any
from backend.benchmark import benchmark_repo
from backend.orchestrator import orchestrator
from backend.agents import SingleLLMBaseline
from backend.memory import long_loop_memory
from backend.schemas import StartDebateRequest


def _score_choice(chosen: str, scenario: Dict[str, Any]) -> tuple[int, float]:
    """Returns (exact_match_int, weighted_quality_score)."""
    c = (chosen or "").strip().lower()
    expert = scenario["expert_choice"].strip().lower()
    secondary = scenario.get("acceptable_secondary", "").strip().lower()
    if c == expert or expert in c or c in expert:
        return 1, 1.0
    if secondary and (c == secondary or secondary in c or c in secondary):
        return 0, 0.5
    return 0, 0.0


class EvaluationEngine:
    """
    Executes Experiment A (Council vs. Single-LLM Baselines - Slide 11)
    and Experiment B (Before vs. After Feedback Learning Curve on Held-Out Test Set - Slide 12).
    """

    async def run_experiment_a(self, use_fast_sim: bool = True) -> Dict[str, Any]:
        """
        Experiment A: Compares each Single LLM alone (no agents, no debate, no memory)
        against the Architect Council (Untrained vs. Feedback-Trained) on the 12 Held-Out Test Scenarios.
        """
        test_scenarios = benchmark_repo.get_test_split()
        feedback_scenarios = benchmark_repo.get_feedback_split()
        active_pool = orchestrator.get_agent_pool()

        # 1. Evaluate Single-LLM Baselines (each LLM family alone)
        baselines_summary: List[Dict[str, Any]] = []
        for agent_cfg in active_pool:
            if not agent_cfg.get("enabled", True):
                continue
            exact_hits = 0
            quality_sum = 0.0
            tradeoff_sum = 0
            citation_sum = 0
            latency_sum = 0.0
            scenario_results = []

            for scen in test_scenarios:
                res = await SingleLLMBaseline.run_single_prompt(
                    provider=agent_cfg["provider"],
                    model=agent_cfg["model"],
                    llm_family=agent_cfg["llm_family"],
                    prompt=scen["prompt"],
                    candidate_options=scen["options"],
                    prefer_fast_sim=use_fast_sim,
                )
                exact, q_score = _score_choice(res["selected_option"], scen)
                exact_hits += exact
                quality_sum += q_score
                tradeoff_sum += res["tradeoff_count"]
                citation_sum += res["citation_count"]
                latency_sum += res["latency_ms"]
                scenario_results.append(
                    {
                        "scenario_id": scen["id"],
                        "selected_option": res["selected_option"],
                        "expert_choice": scen["expert_choice"],
                        "exact_match": bool(exact),
                        "quality_score": q_score,
                    }
                )

            n = max(1, len(test_scenarios))
            baselines_summary.append(
                {
                    "system_name": f"Single LLM: {agent_cfg['llm_family']} ({agent_cfg['model']})",
                    "system_type": "baseline_single_llm",
                    "accuracy_pct": round((exact_hits / n) * 100.0, 1),
                    "weighted_quality_pct": round((quality_sum / n) * 100.0, 1),
                    "avg_tradeoffs": round(tradeoff_sum / n, 2),
                    "avg_citations": round(citation_sum / n, 2),
                    "avg_latency_ms": round(latency_sum / n, 1),
                    "llm_calls_per_decision": 1,
                    "details": scenario_results,
                }
            )

        # 2. Evaluate Architect Council (Untrained — Memory Reset, Debate + KB only)
        long_loop_memory.reset()
        untrained_council = await self._evaluate_council_on_split(
            test_scenarios,
            system_name="Architect Council (Debate + KB, Prior to Feedback)",
            use_long_loop_memory=False,
            use_fast_sim=use_fast_sim,
        )

        # 3. Train Long-Loop Memory on the 12 Feedback Set scenarios (never on Test Set!)
        await self._train_council_on_feedback_set(feedback_scenarios, use_fast_sim=use_fast_sim)

        # 4. Evaluate Architect Council (Full System: Debate + KB + Long-Loop Feedback Memory)
        trained_council = await self._evaluate_council_on_split(
            test_scenarios,
            system_name="Architect Council (Full: Debate + KB + Feedback Loop)",
            use_long_loop_memory=True,
            use_fast_sim=use_fast_sim,
        )

        best_single_acc = max([b["accuracy_pct"] for b in baselines_summary], default=0.0)
        gain_over_best_single = round(trained_council["accuracy_pct"] - best_single_acc, 1)

        return {
            "experiment": "Experiment A — Architect Council vs. Single-LLM Baselines",
            "test_set_size": len(test_scenarios),
            "best_single_llm_accuracy_pct": best_single_acc,
            "council_untrained_accuracy_pct": untrained_council["accuracy_pct"],
            "council_full_accuracy_pct": trained_council["accuracy_pct"],
            "gain_over_best_single_pct": gain_over_best_single,
            "systems": baselines_summary + [untrained_council, trained_council],
        }

    async def run_experiment_b(self, use_fast_sim: bool = True) -> Dict[str, Any]:
        """
        Experiment B (Slide 12): Prove decisions get measurably more accurate after feedback.
        - Benchmark: 24 scenarios split into 12 Feedback Set / 12 Held-Out Test Set.
        - Evaluates on Held-Out Test Set across 4 learning checkpoints:
          * Iteration 0: 0 feedback scenarios (Untrained baseline council)
          * Iteration 1: After 4 feedback scenarios (SCEN-01..04)
          * Iteration 2: After 8 feedback scenarios (SCEN-01..08)
          * Iteration 3: After 12 feedback scenarios (SCEN-01..12)
        """
        feedback_scenarios = benchmark_repo.get_feedback_split()
        test_scenarios = benchmark_repo.get_test_split()

        long_loop_memory.reset()
        learning_curve: List[Dict[str, Any]] = []

        # Checkpoint 0: Before Feedback (0 training scenarios)
        eval_0 = await self._evaluate_council_on_split(
            test_scenarios,
            system_name="Iteration 0 (0 Feedback Scenarios — Before Feedback)",
            use_long_loop_memory=True,
            use_fast_sim=use_fast_sim,
        )
        learning_curve.append(
            {
                "iteration": 0,
                "feedback_scenarios_seen": 0,
                "learned_principles_count": len(long_loop_memory.state.get("learned_principles", [])),
                "accuracy_pct": eval_0["accuracy_pct"],
                "weighted_quality_pct": eval_0["weighted_quality_pct"],
                "avg_consensus_pct": eval_0["avg_consensus_pct"],
                "trust_weights": long_loop_memory.get_trust_weights(),
                "test_results": eval_0["details"],
            }
        )

        # Progressive feedback batches of 4 scenarios each (on Feedback Set ONLY)
        batch_size = 4
        for step_idx, start_i in enumerate(range(0, len(feedback_scenarios), batch_size), start=1):
            batch = feedback_scenarios[start_i : start_i + batch_size]
            await self._train_council_on_feedback_set(batch, use_fast_sim=use_fast_sim)

            seen_count = min(start_i + batch_size, len(feedback_scenarios))
            eval_step = await self._evaluate_council_on_split(
                test_scenarios,
                system_name=f"Iteration {step_idx} (After {seen_count} Feedback Scenarios)",
                use_long_loop_memory=True,
                use_fast_sim=use_fast_sim,
            )
            learning_curve.append(
                {
                    "iteration": step_idx,
                    "feedback_scenarios_seen": seen_count,
                    "learned_principles_count": len(long_loop_memory.state.get("learned_principles", [])),
                    "accuracy_pct": eval_step["accuracy_pct"],
                    "weighted_quality_pct": eval_step["weighted_quality_pct"],
                    "avg_consensus_pct": eval_step["avg_consensus_pct"],
                    "trust_weights": long_loop_memory.get_trust_weights(),
                    "test_results": eval_step["details"],
                }
            )

        before_acc = learning_curve[0]["accuracy_pct"]
        after_acc = learning_curve[-1]["accuracy_pct"]
        return {
            "experiment": "Experiment B — Held-Out Test Set Accuracy Before vs. After Feedback Loop",
            "feedback_set_size": len(feedback_scenarios),
            "held_out_test_set_size": len(test_scenarios),
            "accuracy_before_feedback_pct": before_acc,
            "accuracy_after_feedback_pct": after_acc,
            "accuracy_improvement_pct": round(after_acc - before_acc, 1),
            "final_trust_weights": long_loop_memory.get_trust_weights(),
            "learned_principles": long_loop_memory.state.get("learned_principles", []),
            "learning_curve": learning_curve,
        }

    async def _train_council_on_feedback_set(
        self,
        scenarios: List[Dict[str, Any]],
        use_fast_sim: bool = True,
    ) -> None:
        """Runs debate on Feedback Set scenarios and applies expert human decision to Long-Loop Memory."""
        for scen in scenarios:
            session = await orchestrator.run_debate(
                StartDebateRequest(
                    scenario_id=scen["id"],
                    title=scen["title"],
                    requirements_prompt=scen["prompt"],
                    candidate_options=scen["options"],
                    quality_attributes=scen["quality_attributes"],
                    constraints=scen["constraints"],
                    max_critique_rounds=1,
                    use_long_loop_memory=True,
                ),
                prefer_fast_sim=use_fast_sim,
            )
            latest_msgs = orchestrator._latest_agent_messages.get(session.session_id, {})
            agent_votes = {
                aid: (m.contract.selected_option if m.contract else "")
                for aid, m in latest_msgs.items()
            }
            long_loop_memory.record_human_decision(
                session_id=session.session_id,
                scenario_title=scen["title"],
                requirements_prompt=scen["prompt"],
                final_chosen_option=scen["expert_choice"],
                human_rationale=scen["expert_rationale"],
                agent_votes=agent_votes,
                extracted_principle=f"[{scen['domain']}] {scen['expert_rationale']}",
                trigger_tags=scen["constraints"] + scen["quality_attributes"],
            )

    async def _evaluate_council_on_split(
        self,
        scenarios: List[Dict[str, Any]],
        system_name: str,
        use_long_loop_memory: bool,
        use_fast_sim: bool,
    ) -> Dict[str, Any]:
        exact_hits = 0
        quality_sum = 0.0
        tradeoff_sum = 0
        citation_sum = 0
        latency_sum = 0.0
        consensus_sum = 0.0
        details = []

        for scen in scenarios:
            session = await orchestrator.run_debate(
                StartDebateRequest(
                    scenario_id=scen["id"],
                    title=scen["title"],
                    requirements_prompt=scen["prompt"],
                    candidate_options=scen["options"],
                    quality_attributes=scen["quality_attributes"],
                    constraints=scen["constraints"],
                    max_critique_rounds=1,
                    use_long_loop_memory=use_long_loop_memory,
                ),
                prefer_fast_sim=use_fast_sim,
            )
            chosen = session.adr.chosen_option if session.adr else ""
            exact, q_score = _score_choice(chosen, scen)
            exact_hits += exact
            quality_sum += q_score
            tradeoff_sum += len(session.adr.tradeoffs) if session.adr else 0
            citation_sum += len(session.adr.citations) if session.adr else 0
            latency_sum += session.total_latency_ms
            consensus_sum += (session.adr.consensus_score * 100.0) if session.adr else 0.0
            details.append(
                {
                    "scenario_id": scen["id"],
                    "title": scen["title"],
                    "selected_option": chosen,
                    "expert_choice": scen["expert_choice"],
                    "exact_match": bool(exact),
                    "quality_score": q_score,
                    "consensus_type": session.adr.consensus_type if session.adr else "NONE",
                    "consensus_pct": round((session.adr.consensus_score * 100.0), 1) if session.adr else 0.0,
                    "dissent_count": len(session.adr.minority_dissent) if session.adr else 0,
                    "citations": session.adr.citations if session.adr else [],
                }
            )

        n = max(1, len(scenarios))
        active_count = len(orchestrator.get_active_agents())
        return {
            "system_name": system_name,
            "system_type": "architect_council",
            "accuracy_pct": round((exact_hits / n) * 100.0, 1),
            "weighted_quality_pct": round((quality_sum / n) * 100.0, 1),
            "avg_tradeoffs": round(tradeoff_sum / n, 2),
            "avg_citations": round(citation_sum / n, 2),
            "avg_consensus_pct": round(consensus_sum / n, 1),
            "avg_latency_ms": round(latency_sum / n, 1),
            "llm_calls_per_decision": active_count * 2,
            "details": details,
        }


evaluation_engine = EvaluationEngine()

