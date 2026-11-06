import pytest
from backend.orchestrator import orchestrator
from backend.schemas import (
    StartDebateRequest,
    ShortLoopFeedbackRequest,
    LongLoopDecisionRequest,
    AgentConfigModel,
    DebatePhase,
)
from backend.memory import long_loop_memory
from backend.evaluator import evaluation_engine
from backend.benchmark import benchmark_repo


@pytest.mark.asyncio
async def test_five_phase_debate_and_short_long_feedback_loops():
    """Verifies Pillar 1, Pillar 2 (5-phase debate & typed A2A trace), and Pillar 3 (Short & Long loops)."""
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

    # Check all 5 phases occurred in messages
    phases_present = {m.phase for m in session.messages}
    assert DebatePhase.FRAME in phases_present
    assert DebatePhase.PROPOSE in phases_present
    assert DebatePhase.CRITIQUE in phases_present
    assert DebatePhase.CONVERGE in phases_present
    assert DebatePhase.DECIDE in phases_present
    assert session.adr is not None
    assert len(session.adr.citations) > 0

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

    # Test Long-Loop Human Final Decision Learning
    ll_res = orchestrator.apply_long_loop_decision(
        LongLoopDecisionRequest(
            session_id=session.session_id,
            final_chosen_option=scen["expert_choice"],
            human_rationale=scen["expert_rationale"],
        )
    )
    assert ll_res["learning_update"]["total_learned_principles"] == 1
    assert ll_res["learning_update"]["updated_trust_weights"]["agent_pragmatist"] > 1.0


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
        model="llama-3.1-8b-instant",
        mandate="Full architect prioritizing cryptographic workload identity and compliance.",
        priorities=["security", "integrity"],
        enabled=True,
    )
    updated_pool = orchestrator.add_or_update_agent(new_agent)
    assert len(updated_pool) == initial_count + 1
    orchestrator.reset_agent_pool()


@pytest.mark.asyncio
async def test_experiment_a_and_experiment_b():
    """Verifies Slide 11 (Experiment A: Council beats Single LLM) & Slide 12 (Experiment B: Feedback improves accuracy)."""
    exp_a = await evaluation_engine.run_experiment_a(use_fast_sim=True)
    assert exp_a["council_full_accuracy_pct"] > exp_a["best_single_llm_accuracy_pct"]
    assert exp_a["gain_over_best_single_pct"] > 0

    exp_b = await evaluation_engine.run_experiment_b(use_fast_sim=True)
    assert exp_b["feedback_set_size"] == 12
    assert exp_b["held_out_test_set_size"] == 12
    assert exp_b["accuracy_after_feedback_pct"] > exp_b["accuracy_before_feedback_pct"]
    assert exp_b["accuracy_improvement_pct"] > 0

