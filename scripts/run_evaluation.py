"""
Standalone CLI Runner for Experiment A (Council vs. Single-LLM Baselines)
and Experiment B (Held-Out Test Set Learning Curve Before vs. After Feedback).

Usage:
    python scripts/run_evaluation.py
"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.evaluator import evaluation_engine


async def main() -> None:
    print("=" * 80)
    print("AI ASSISTED SOFTWARE ARCHITECTING COUNCIL — EVALUATION SUITE")
    print("=" * 80)

    print("\n[1/2] Running Experiment A: Architect Council vs. Single-LLM Baselines...")
    exp_a = await evaluation_engine.run_experiment_a(use_fast_sim=True)
    print(f"  -> Held-Out Test Set Size: {exp_a['test_set_size']} scenarios")
    print(f"  -> Best Single LLM Accuracy: {exp_a['best_single_llm_accuracy_pct']}%")
    print(f"  -> Full Council Accuracy:    {exp_a['council_full_accuracy_pct']}%")
    print(f"  -> Council Gain over Single: +{exp_a['gain_over_best_single_pct']}%\n")

    print(f"{'System Name':<56} | {'Accuracy':<9} | {'Quality':<9} | {'Trade-offs':<10} | {'Citations'}")
    print("-" * 100)
    for s in exp_a["systems"]:
        print(
            f"{s['system_name']:<56} | {str(s['accuracy_pct'])+'%':<9} | "
            f"{str(s['weighted_quality_pct'])+'%':<9} | {s['avg_tradeoffs']:<10} | {s['avg_citations']}"
        )

    print("\n" + "=" * 80)
    print("[2/2] Running Experiment B: Feedback Loop Learning Curve (Held-Out Test Set)...")
    exp_b = await evaluation_engine.run_experiment_b(use_fast_sim=True)
    print(f"  -> Feedback Set: {exp_b['feedback_set_size']} scenarios | Held-Out Test Set: {exp_b['held_out_test_set_size']} scenarios")
    print(f"  -> Accuracy Before Feedback (Iter 0): {exp_b['accuracy_before_feedback_pct']}%")
    print(f"  -> Accuracy After Feedback  (Iter 3): {exp_b['accuracy_after_feedback_pct']}%")
    print(f"  -> Net Learning Improvement:          +{exp_b['accuracy_improvement_pct']}%\n")

    print(f"{'Checkpoint':<18} | {'Feedback Seen':<15} | {'Learned Principles':<18} | {'Test Accuracy':<14} | {'Consensus'}")
    print("-" * 85)
    for c in exp_b["learning_curve"]:
        print(
            f"Iteration {c['iteration']:<8} | {c['feedback_scenarios_seen']:<15} | "
            f"{c['learned_principles_count']:<18} | {str(c['accuracy_pct'])+'%':<14} | {c['avg_consensus_pct']}%"
        )

    out_path = ROOT / "data" / "latest_evaluation_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"experiment_a": exp_a, "experiment_b": exp_b}, f, indent=2)
    print(f"\nSaved full JSON results to: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())

