from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import uuid


class DebatePhase(str, Enum):
    FRAME = "FRAME"
    PROPOSE = "PROPOSE"
    CRITIQUE = "CRITIQUE"
    CONVERGE = "CONVERGE"
    DECIDE = "DECIDE"
    HUMAN_FEEDBACK = "HUMAN_FEEDBACK"


class MessageType(str, Enum):
    CONTEXT_FRAME = "CONTEXT_FRAME"
    INITIAL_PROPOSAL = "INITIAL_PROPOSAL"
    PEER_CRITIQUE = "PEER_CRITIQUE"
    REVISED_POSITION = "REVISED_POSITION"
    CONVERGENCE_VOTE = "CONVERGENCE_VOTE"
    ADR_DECISION = "ADR_DECISION"
    HUMAN_INTERVENTION = "HUMAN_INTERVENTION"


class AgentOutputContract(BaseModel):
    """Mandatory output contract shared by all peer architect agents (Slide 5)."""
    selected_option: str = Field(..., min_length=1, description="The architectural option chosen by the agent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    summary_argument: str = Field(..., min_length=1, description="Core architectural argument justifying the choice")
    evaluated_options: List[str] = Field(default_factory=list, description="Options explicitly analyzed")
    tradeoffs: Dict[str, str] = Field(
        default_factory=dict,
        description="Quality attribute trade-offs (e.g. {'Latency vs Operability': '...'})",
    )
    citations: List[str] = Field(
        default_factory=list,
        description="Knowledge Base IDs or Learned Principle IDs cited as evidence (e.g. ['KB-PAT-01', 'KB-ADR-01'])",
    )
    challenged_agents: List[str] = Field(
        default_factory=list,
        description="IDs of peer agents challenged during critique rounds",
    )
    critique_points: List[str] = Field(
        default_factory=list,
        description="Specific technical objections or responses to peers",
    )
    mind_changed: bool = Field(
        default=False,
        description="Whether the agent changed its selected option compared to the previous round",
    )
    change_reason: Optional[str] = Field(
        default=None,
        description="Argument that convinced the agent to change its mind (if mind_changed=True)",
    )


class A2AMessage(BaseModel):
    """Structured, typed, traceable Agent-to-Agent message schema (Slide 8)."""
    message_id: str = Field(default_factory=lambda: f"msg-{uuid.uuid4().hex[:8]}")
    session_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    phase: DebatePhase
    round_num: int = 0
    sender_id: str
    sender_name: str
    sender_role: str
    sender_stance: str
    llm_family: str
    llm_model: str
    llm_provider: str
    recipient_id: str = "ALL_COUNCIL"
    reply_to_ids: List[str] = Field(default_factory=list)
    message_type: MessageType
    content: str
    contract: Optional[AgentOutputContract] = None
    latency_ms: float = 0.0
    execution_mode: str = "live"


class DissentRecord(BaseModel):
    """Captures minority views so dissent is never lost (Slide 7 & Miccio et al., 2026)."""
    agent_id: str
    agent_name: str
    stance: str
    llm_family: str
    preferred_option: str
    rationale: str
    citations: List[str] = Field(default_factory=list)


class ConsideredOptionMADR(BaseModel):
    """
    MADR-compliant structured evaluation of each considered architectural option
    including rejected alternatives (Miccio, Tommasel, Díaz-Pace, 2026 - ADRminer).
    """
    option_name: str = Field(..., min_length=1, description="Canonical name of the candidate option")
    pros: List[str] = Field(..., min_length=1, description="Explicit positive consequences / arguments in favor")
    cons: List[str] = Field(..., min_length=1, description="Explicit negative consequences / rejection reasons")
    is_chosen: bool = Field(default=False, description="True if this option was selected as the final decision")


class ADRDecision(BaseModel):
    """
    MADR-compliant Architecture Decision Record synthesized by the Chair Agent
    (Slide 7 & 13; Miccio, Tommasel, Díaz-Pace, 2026).
    """
    adr_id: str = Field(default_factory=lambda: f"ADR-{uuid.uuid4().hex[:6].upper()}")
    title: str = Field(..., min_length=3)
    status: str = "PROPOSED"
    context_and_problem: str = Field(..., min_length=5)
    decision_drivers: List[str] = Field(
        ...,
        min_length=1,
        description="Mandatory non-empty list of ISO/IEC 25010 decision drivers & constraints",
    )
    quality_attributes: List[str] = Field(..., min_length=1)
    considered_options: List[str] = Field(..., min_length=2)
    options_analysis: List[ConsideredOptionMADR] = Field(
        ...,
        min_length=1,
        description="Structured MADR pros/cons evaluation for the chosen option and all rejected alternatives",
    )
    chosen_option: str = Field(..., min_length=1)
    consensus_type: str  # "UNANIMOUS", "SUPERMAJORITY", "WEIGHTED_MAJORITY", "CHAIR_TIE_BREAK"
    consensus_score: float
    rationale: str = Field(..., min_length=5)
    tradeoffs: Dict[str, str]
    citations: List[str]
    vote_breakdown: Dict[str, str]
    weighted_scores: Dict[str, float]
    minority_dissent: List[DissentRecord] = Field(default_factory=list)
    validation_gate_passed: bool = True
    validation_notes: List[str] = Field(default_factory=list)
    human_approved: Optional[bool] = None
    human_final_decision: Optional[str] = None
    human_notes: Optional[str] = None


class DebateSession(BaseModel):
    """Complete state of a Council Debate session."""
    session_id: str
    scenario_id: Optional[str] = None
    title: str
    requirements_prompt: str
    candidate_options: List[str] = Field(default_factory=list)
    quality_attributes: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    retrieved_kb_items: List[Dict[str, Any]] = Field(default_factory=list)
    applied_learned_principles: List[Dict[str, Any]] = Field(default_factory=list)
    messages: List[A2AMessage] = Field(default_factory=list)
    adr: Optional[ADRDecision] = None
    short_loop_iterations: int = 0
    total_latency_ms: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StartDebateRequest(BaseModel):
    scenario_id: Optional[str] = None
    title: Optional[str] = None
    requirements_prompt: str
    candidate_options: Optional[List[str]] = None
    quality_attributes: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    max_critique_rounds: int = 2
    use_long_loop_memory: bool = True


class ShortLoopFeedbackRequest(BaseModel):
    session_id: str
    human_critique: str
    emphasized_quality_attributes: List[str] = Field(default_factory=list)
    new_constraint: Optional[str] = None


class LongLoopDecisionRequest(BaseModel):
    session_id: str
    final_chosen_option: str
    human_rationale: str
    extracted_principle: Optional[str] = None
    trigger_tags: List[str] = Field(default_factory=list)


class AgentConfigModel(BaseModel):
    agent_id: str
    name: str
    stance: str
    icon: str = "🤖"
    color: str = "#38bdf8"
    llm_family: str
    provider: str
    model: str
    temperature: float = 0.3
    mandate: str
    priorities: List[str] = Field(default_factory=list)
    enabled: bool = True
