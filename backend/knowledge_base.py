import json
import re
from pathlib import Path
from typing import List, Dict, Any
from backend.config import settings


class KnowledgeBase:
    """
    Shared Architectural Knowledge Base with Provenance Tracking (Slide 9).
    Contains ISO/IEC 25010 quality attributes, Architectural Patterns, Tactics,
    and Organizational ADRs. Every LLM in the council queries the exact same KB
    to guarantee a fair, grounded debate.
    """

    def __init__(self, kb_path: Path = None) -> None:
        self.kb_path = kb_path or (settings.DATA_DIR / "knowledge_items.json")
        self.items: List[Dict[str, Any]] = []
        self.items_by_id: Dict[str, Dict[str, Any]] = {}
        self.reload()

    def reload(self) -> None:
        if self.kb_path.exists():
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.items = json.load(f)
            self.items_by_id = {item["id"]: item for item in self.items}

    def retrieve(
        self,
        query: str,
        quality_attributes: List[str] = None,
        constraints: List[str] = None,
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:
        """Retrieves the most relevant KB items with provenance metadata."""
        quality_attributes = [q.lower() for q in (quality_attributes or [])]
        constraints = [c.lower() for c in (constraints or [])]
        tokens = set(re.findall(r"[a-z0-9\-]+", query.lower()))
        for c in constraints:
            tokens.update(re.findall(r"[a-z0-9\-]+", c))

        scored: List[tuple[float, Dict[str, Any]]] = []
        for item in self.items:
            score = 0.0
            item_tags = [t.lower() for t in item.get("tags", [])]
            item_qas = [q.lower() for q in item.get("quality_attributes", [])]
            text_blob = f"{item['title']} {item['summary']} {' '.join(item_tags)}".lower()

            # Tag & token overlap
            for tok in tokens:
                if len(tok) < 3:
                    continue
                if tok in item_tags:
                    score += 3.0
                elif tok in text_blob:
                    score += 1.2

            # Quality attribute match
            for qa in quality_attributes:
                if qa in item_qas or qa in text_blob:
                    score += 2.5

            # Constraint match
            for c in constraints:
                if any(part in item_tags for part in c.split()):
                    score += 2.5

            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [item for score, item in scored[:top_k] if score > 0]
        if len(selected) < 3:
            selected = [item for _, item in scored[:3]]
        return selected

    def resolve_citations(self, citation_ids: List[str]) -> List[Dict[str, Any]]:
        """Verifies and resolves citation IDs to their full provenance records."""
        resolved = []
        for cid in citation_ids:
            clean_id = cid.strip().strip("[]")
            if clean_id in self.items_by_id:
                resolved.append(self.items_by_id[clean_id])
        return resolved


knowledge_base = KnowledgeBase()

