import pytest
from backend.orchestrator import orchestrator
from backend.schemas import (
    StartDebateRequest,
    ShortLoopFeedbackRequest,
    LongLoopDecisionRequest,
    AgentConfigModel,
    DebatePhase,
)
from backend.knowledge_base import knowledge_base
from backend.memory import long_loop_memory
from backend.evaluator import evaluation_engine
from backend.benchmark import benchmark_repo


def test_check1_kb_decision_layer_and_select_reject_filtering():
    """Verifies Check 1 (Nishio, Washizaki, Muccini et al., 2026): structured KB & Select/Reject constraint filtering."""
    for item in knowledge_base.items:
        assert "problem" in item and len(item["problem"]) > 5
        assert "decision_drivers" in item and len(item["decision_drivers"]) >= 1
        assert "options" in item and len(item["options"]) >= 1
        assert "selection_conditions" in item and len(item["selection_conditions"]) >= 1
        assert "rejection_conditions" in item and len(item["rejection_conditions"]) >= 1

    # When querying for 'small-team' and 'on-prem' event streaming, KB-PAT-01 (NATS/Redpanda) must rank above KB-PAT-02 (Kafka)
    results = knowledge_base.retrieve(
        query="event ingestion streaming for factory tools",
        quality_attributes=["latency", "operability"],
        constraints=["small-team", "on-prem", "<1s latency"],
        top_k=5,
    )
    retrieved_ids = [r["id"] for r in results]
    assert "KB-PAT-01" in retrieved_ids
    if "KB-PAT-02" in retrieved_ids:
        assert retrieved_ids.index("KB-PAT-01") < retrieved_ids.index("KB-PAT-02")


@pytest.mark.asyncio
async def test_check2_and_check4_madr_compliance_and_validation_gate():
    """Verifies Check 2 (MADR schema pros/cons, decision_drivers) & Check 4 (Parallel Propose + ADR Validation Gate)."""
    long_loop_memory.reset()
    orchestrator.reset_agent_pool()

    scen = benchmark_repo.get_by_id("SCEN-01")
    assert scen is not None

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
        prefer_fast_sim=True,
    )

    phases_present = {m.phase for m in session.messages}
    assert DebatePhase.FRAME in phases_present
    assert DebatePhase.PROPOSE in phases_present
    assert DebatePhase.CRITIQUE in phases_present
    assert DebatePhase.CONVERGE in phases_present
    assert DebatePhase.DECIDE in phases_present

    adr = session.adr
    assert adr is not None
    # Check 2: MADR mandatory fields & pros/cons on all considered options
    assert len(adr.decision_drivers) >= 1
    assert len(adr.considered_options) >= 2
    assert len(adr.options_analysis) == len(scen["options"])
    for opt_eval in adr.options_analysis:
        assert len(opt_eval.pros) >= 1
        assert len(opt_eval.cons) >= 1
    # Check 4: Validation Gate passed
    assert adr.validation_gate_passed is True
    assert len(adr.validation_notes) >= 1

    # Test Short-Loop Human Feedback Revision
    revised_session = await orchestrator.apply_short_loop_feedback(
        ShortLoopFeedbackRequest(
            session_id=session.session_id,
            human_critique="We have only 3 ops engineers and zero JVM expertise; favor NATS JetStream single-binary.",
            emphasized_quality_attributes=["operability"],
        ),
        prefer_fast_sim=True,
    )
    assert revised_session.short_loop_iterations == 1
    assert revised_session.adr.chosen_option == scen["expert_choice"]

    # Test Long-Loop Human Final Decision Learning & Check 3 (Last_K + RAFG retrieval)
    ll_res = orchestrator.apply_long_loop_decision(
        LongLoopDecisionRequest(
            session_id=session.session_id,
            final_chosen_option=scen["expert_choice"],
            human_rationale=scen["expert_rationale"],
        )
    )
    assert ll_res["learning_update"]["total_learned_principles"] == 1
    assert ll_res["learning_update"]["updated_trust_weights"]["agent_pragmatist"] > 1.0

    retrieved_mem = long_loop_memory.retrieve_relevant_principles(
        prompt="3,000 cameras on-prem <500ms latency small team",
        quality_attributes=["latency", "operability"],
        constraints=["on-prem", "small-team"],
        last_k=3,
        rafg_k=3,
    )
    assert len(retrieved_mem) == 1


def test_agent_swappability_without_rewrites():
    """Verifies Slide 8 requirement: 'Swappable — add an agent without rewrites'."""
    orchestrator.reset_agent_pool()
    initial_count = len(orchestrator.get_agent_pool())

    new_agent = AgentConfigModel(
        agent_id="agent_sec_specialist",
        name="Zero-Trust Architect",
        stance="Security-Hawk",
        llm_family="Mistral Family",
        provider="groq",
        model="openai/gpt-oss-20b",
        mandate="Full architect prioritizing cryptographic workload identity and compliance.",
        priorities=["security", "integrity"],
        enabled=True,
    )
    updated_pool = orchestrator.add_or_update_agent(new_agent)
    assert len(updated_pool) == initial_count + 1
    orchestrator.reset_agent_pool()


@pytest.mark.asyncio
async def test_check5_experiment_a_and_experiment_b_with_driver_coverage():
    """Verifies Check 5: Experiment A, Experiment B, Decision Accuracy & Driver Coverage."""
    exp_a = await evaluation_engine.run_experiment_a(use_fast_sim=True)
    assert exp_a["council_full_accuracy_pct"] > exp_a["best_single_llm_accuracy_pct"]
    assert exp_a["gain_over_best_single_pct"] > 0
    full_council_sys = exp_a["systems"][-1]
    assert full_council_sys["avg_driver_coverage_pct"] == 100.0

    exp_b = await evaluation_engine.run_experiment_b(use_fast_sim=True)
    assert exp_b["feedback_set_size"] == 12
    assert exp_b["held_out_test_set_size"] == 12
    assert exp_b["accuracy_after_feedback_pct"] > exp_b["accuracy_before_feedback_pct"]
    assert exp_b["accuracy_improvement_pct"] > 0
