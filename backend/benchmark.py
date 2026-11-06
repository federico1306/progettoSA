import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import settings


class BenchmarkRepository:
    """Loads the 24 curated Architectural Scenarios (12 Feedback Set + 12 Held-Out Test Set)."""

    def __init__(self, path: Path = None) -> None:
        self.path = path or (settings.DATA_DIR / "benchmark_scenarios.json")
        self.scenarios: List[Dict[str, Any]] = []
        self.by_id: Dict[str, Dict[str, Any]] = {}
        self.reload()

    def reload(self) -> None:
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                self.scenarios = json.load(f)
            self.by_id = {s["id"]: s for s in self.scenarios}

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.scenarios)

    def get_by_id(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        return self.by_id.get(scenario_id)

    def get_feedback_split(self) -> List[Dict[str, Any]]:
        return [s for s in self.scenarios if s.get("split") == "feedback"]

    def get_test_split(self) -> List[Dict[str, Any]]:
        return [s for s in self.scenarios if s.get("split") == "test"]


benchmark_repo = BenchmarkRepository()

