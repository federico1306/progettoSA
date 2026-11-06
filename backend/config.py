import os
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


class Settings:
    PROJECT_TITLE: str = "AI Assisted Software Architecting Council"
    COURSE: str = "Software Architecture 2026/27 — Prof. H. Muccini, A. Di Paolo (Micron), D. Spinosi (Micron)"
    TEAM_MEMBERS: List[str] = [
        "Studente 1 (Nome Cognome - Matricola)",
        "Studente 2 (Nome Cognome - Matricola)",
        "Studente 3 (Nome Cognome - Matricola)",
        "Studente 4 (Nome Cognome - Matricola)",
    ]

    LLM_MODE: str = os.getenv("LLM_MODE", "auto")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()

    MAX_CRITIQUE_ROUNDS: int = int(os.getenv("MAX_CRITIQUE_ROUNDS", "2"))
    CONSENSUS_THRESHOLD: float = float(os.getenv("CONSENSUS_THRESHOLD", "0.65"))
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    DATA_DIR: Path = BASE_DIR / "data"
    DOCS_DIR: Path = BASE_DIR / "docs"


settings = Settings()

# Default Swappable Council Pool (Pillar 1: >=3 distinct LLM families + distinct Stances)
DEFAULT_AGENT_POOL: List[Dict[str, Any]] = [
    {
        "agent_id": "agent_pragmatist",
        "name": "Pragmatist Architect",
        "role": "peer_architect",
        "stance": "Pragmatist",
        "icon": "⚙️",
        "color": "#60a5fa",
        "llm_family": "OpenAI GPT-OSS Family",
        "provider": os.getenv("AGENT_PRAGMATIST_PROVIDER", "groq"),
        "model": os.getenv("AGENT_PRAGMATIST_MODEL", "openai/gpt-oss-120b"),
        "temperature": 0.3,
        "mandate": (
            "Full software architect with a Pragmatist temperament. You value the simplest architecture "
            "that works, rapid time-to-market, low operational cognitive load, and alignment with small team skills."
        ),
        "priorities": ["operability", "simplicity", "time-to-market", "cost"],
        "enabled": True,
    },
    {
        "agent_id": "agent_guardian",
        "name": "Guardian Architect",
        "role": "peer_architect",
        "stance": "Guardian",
        "icon": "🛡️",
        "color": "#f87171",
        "llm_family": "Google Gemini Family",
        "provider": os.getenv("AGENT_GUARDIAN_PROVIDER", "gemini"),
        "model": os.getenv("AGENT_GUARDIAN_MODEL", "gemini-2.5-flash"),
        "temperature": 0.2,
        "mandate": (
            "Full software architect with a Guardian temperament. You are risk-averse and prioritize proven "
            "battle-tested technologies, strict reliability, fault tolerance, data sovereignty, and security."
        ),
        "priorities": ["reliability", "security", "availability", "auditability"],
        "enabled": True,
    },
    {
        "agent_id": "agent_innovator",
        "name": "Innovator Architect",
        "role": "peer_architect",
        "stance": "Innovator",
        "icon": "🚀",
        "color": "#c084fc",
        "llm_family": "Alibaba Qwen Family",
        "provider": os.getenv("AGENT_INNOVATOR_PROVIDER", "groq"),
        "model": os.getenv("AGENT_INNOVATOR_MODEL", "qwen/qwen3.8-27b"),
        "temperature": 0.5,
        "mandate": (
            "Full software architect with an Innovator temperament. You champion future-proof architectures, "
            "high throughput, modern cloud-native or high-performance engines, and long-term evolvability."
        ),
        "priorities": ["scalability", "evolvability", "latency", "throughput"],
        "enabled": True,
    },
    {
        "agent_id": "agent_skeptic",
        "name": "Skeptic Architect",
        "role": "peer_architect",
        "stance": "Skeptic",
        "icon": "🧐",
        "color": "#fbbf24",
        "llm_family": "GPT-OSS-20B / ALLaM Family",
        "provider": os.getenv("AGENT_SKEPTIC_PROVIDER", "groq"),
        "model": os.getenv("AGENT_SKEPTIC_MODEL", "openai/gpt-oss-20b"),
        "temperature": 0.3,
        "mandate": (
            "Full software architect with a Skeptic temperament. You challenge hype and unsubstantiated claims, "
            "expose hidden operational costs, failure modes, and vendor lock-in, and demand hard KB evidence."
        ),
        "priorities": ["cost", "maintainability", "fault-tolerance", "operability"],
        "enabled": True,
    },
]

CHAIR_AGENT_CONFIG: Dict[str, Any] = {
    "agent_id": "agent_chair",
    "name": "Chair Architect",
    "role": "chair",
    "stance": "Neutral Moderator & Synthesizer",
    "icon": "⚖️",
    "color": "#22c55e",
    "llm_family": "Google Gemini Chair Synthesizer",
    "provider": os.getenv("AGENT_CHAIR_PROVIDER", "gemini"),
    "model": os.getenv("AGENT_CHAIR_MODEL", "gemini-2.5-flash"),
    "temperature": 0.2,
    "mandate": (
        "Chair of the Architecture Review Board. You frame the architectural problem, enforce the debate "
        "protocol, weigh arguments by evidence and learned trust weights, resolve deadlocks, and author the final ADR "
        "while explicitly preserving minority dissent."
    ),
}

