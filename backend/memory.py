import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from backend.config import settings


class LongLoopMemory:
    """
    Pillar 3 — Long-Loop Feedback & Learning Engine (Slide 10 & Slide 12).
    Stores:
    1. Learned Organizational Principles extracted from Human Architect feedback.
    2. Episodic Memory of past human-validated architectural decisions.
    3. Per-Agent / Per-Model Trust Weights updated via reinforcement when agents
       agree or disagree with the Human Architect's final decision.
    """

    def __init__(self, store_path: Path = None) -> None:
        self.store_path = store_path or (settings.DATA_DIR / "memory_store.json")
        self.state: Dict[str, Any] = {
            "version": "1.0",
            "agent_trust_weights": {
                "agent_pragmatist": 1.0,
                "agent_guardian": 1.0,
                "agent_innovator": 1.0,
                "agent_skeptic": 1.0,
            },
            "learned_principles": [],
            "episodic_decisions": [],
            "feedback_history": [],
        }
        self.load()

    def load(self) -> None:
        if self.store_path.exists():
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
            except Exception:
                self.reset()
        else:
            self.save()

    def save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def reset(self) -> Dict[str, Any]:
        """Resets Long-Loop Memory to baseline (untrained) state."""
        self.state = {
            "version": "1.0",
            "agent_trust_weights": {
                "agent_pragmatist": 1.0,
                "agent_guardian": 1.0,
                "agent_innovator": 1.0,
                "agent_skeptic": 1.0,
            },
            "learned_principles": [],
            "episodic_decisions": [],
            "feedback_history": [],
        }
        self.save()
        return self.state

    def get_trust_weights(self) -> Dict[str, float]:
        return dict(self.state.get("agent_trust_weights", {}))

    def retrieve_relevant_principles(
        self,
        prompt: str,
        quality_attributes: List[str] = None,
        constraints: List[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieves learned principles and episodic decisions relevant to the current scenario."""
        principles = self.state.get("learned_principles", [])
        if not principles:
            return []

        blob = f"{prompt} {' '.join(quality_attributes or [])} {' '.join(constraints or [])}".lower()
        tokens = set(re.findall(r"[a-z0-9\-]+", blob))

        scored: List[tuple[float, Dict[str, Any]]] = []
        for p in principles:
            score = 0.0
            tags = [t.lower() for t in p.get("tags", [])]
            p_text = f"{p.get('principle', '')} {p.get('preferred_pattern', '')} {' '.join(tags)}".lower()
            for tok in tokens:
                if len(tok) < 3:
                    continue
                if tok in tags:
                    score += 3.0
                elif tok in p_text:
                    score += 1.0
            if score > 0:
                scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:top_k]]

    def record_human_decision(
        self,
        session_id: str,
        scenario_title: str,
        requirements_prompt: str,
        final_chosen_option: str,
        human_rationale: str,
        agent_votes: Dict[str, str],
        extracted_principle: Optional[str] = None,
        trigger_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Updates Long-Loop Memory from a final Human Architect decision:
        1. Adjusts per-agent trust weights (rewarding agents that matched human choice).
        2. Stores episodic decision record.
        3. Extracts & stores reusable architectural principle for future council debates.
        """
        weights = self.state.setdefault("agent_trust_weights", {})
        for agent_id, voted_opt in agent_votes.items():
            cur = float(weights.get(agent_id, 1.0))
            if voted_opt.strip().lower() == final_chosen_option.strip().lower():
                weights[agent_id] = round(min(2.0, cur + 0.12), 3)
            else:
                weights[agent_id] = round(max(0.55, cur - 0.05), 3)

        principle_id = f"LEARNED-{len(self.state['learned_principles']) + 1:02d}"
        if not trigger_tags:
            trigger_tags = [
                w
                for w in re.findall(r"[a-z0-9\-]+", f"{scenario_title} {requirements_prompt}".lower())
                if len(w) >= 4
            ][:10]

        principle_text = extracted_principle or (
            f"When evaluating '{scenario_title}' patterns ({', '.join(trigger_tags[:5])}), "
            f"prefer '{final_chosen_option}' because: {human_rationale}"
        )

        principle_entry = {
            "id": principle_id,
            "principle": principle_text,
            "preferred_pattern": final_chosen_option,
            "rationale": human_rationale,
            "tags": trigger_tags,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.state["learned_principles"].append(principle_entry)

        decision_entry = {
            "session_id": session_id,
            "scenario_title": scenario_title,
            "final_chosen_option": final_chosen_option,
            "human_rationale": human_rationale,
            "agent_votes": agent_votes,
            "principle_id": principle_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.state["episodic_decisions"].append(decision_entry)
        self.state["feedback_history"].append(decision_entry)
        self.save()
        return {
            "updated_trust_weights": weights,
            "new_principle": principle_entry,
            "total_learned_principles": len(self.state["learned_principles"]),
        }


long_loop_memory = LongLoopMemory()

