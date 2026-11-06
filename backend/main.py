import asyncio
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings, BASE_DIR, CHAIR_AGENT_CONFIG
from backend.schemas import (
    StartDebateRequest,
    ShortLoopFeedbackRequest,
    LongLoopDecisionRequest,
    AgentConfigModel,
)
from backend.orchestrator import orchestrator
from backend.bus import message_bus
from backend.knowledge_base import knowledge_base
from backend.memory import long_loop_memory
from backend.benchmark import benchmark_repo
from backend.evaluator import evaluation_engine
from backend.agents import SingleLLMBaseline

app = FastAPI(
    title=settings.PROJECT_TITLE,
    description=settings.COURSE,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = BASE_DIR / "frontend"


@app.get("/api/meta")
async def get_meta():
    return {
        "project_title": settings.PROJECT_TITLE,
        "course": settings.COURSE,
        "team_members": settings.TEAM_MEMBERS,
        "llm_mode": settings.LLM_MODE,
        "configured_keys": {
            "groq": bool(settings.GROQ_API_KEY),
            "gemini": bool(settings.GEMINI_API_KEY),
            "openrouter": bool(settings.OPENROUTER_API_KEY),
            "openai": bool(settings.OPENAI_API_KEY),
            "anthropic": bool(settings.ANTHROPIC_API_KEY),
        },
        "chair_agent": CHAIR_AGENT_CONFIG,
        "agents": orchestrator.get_agent_pool(),
        "memory_summary": {
            "learned_principles_count": len(long_loop_memory.state.get("learned_principles", [])),
            "episodic_decisions_count": len(long_loop_memory.state.get("episodic_decisions", [])),
            "trust_weights": long_loop_memory.get_trust_weights(),
        },
    }


@app.get("/api/agents")
async def list_agents():
    return {
        "chair": CHAIR_AGENT_CONFIG,
        "agents": orchestrator.get_agent_pool(),
    }


@app.post("/api/agents")
async def upsert_agent(agent: AgentConfigModel):
    updated = orchestrator.add_or_update_agent(agent)
    return {"agents": updated}


@app.patch("/api/agents/{agent_id}/toggle")
async def toggle_agent(agent_id: str, enabled: bool = Query(...)):
    updated = orchestrator.toggle_agent(agent_id, enabled)
    return {"agents": updated}


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    updated = orchestrator.remove_agent(agent_id)
    return {"agents": updated}


@app.post("/api/agents/reset")
async def reset_agents():
    updated = orchestrator.reset_agent_pool()
    return {"agents": updated}


@app.get("/api/knowledge")
async def get_knowledge():
    return {"items": knowledge_base.items}


@app.get("/api/scenarios")
async def get_scenarios():
    return {
        "all": benchmark_repo.get_all(),
        "feedback_split": benchmark_repo.get_feedback_split(),
        "test_split": benchmark_repo.get_test_split(),
    }


@app.get("/api/memory")
async def get_memory():
    return long_loop_memory.state


@app.post("/api/memory/reset")
async def reset_memory():
    return long_loop_memory.reset()


@app.post("/api/debate/start")
async def start_debate(req: StartDebateRequest, fast_sim: bool = Query(default=False)):
    if req.scenario_id and not req.candidate_options:
        scen = benchmark_repo.get_by_id(req.scenario_id)
        if scen:
            req.title = req.title or scen["title"]
            req.requirements_prompt = req.requirements_prompt or scen["prompt"]
            req.candidate_options = scen["options"]
            req.quality_attributes = scen["quality_attributes"]
            req.constraints = scen["constraints"]

    session = await orchestrator.run_debate(req, prefer_fast_sim=fast_sim)
    return session.model_dump()


@app.post("/api/debate/short-loop")
async def short_loop_feedback(req: ShortLoopFeedbackRequest, fast_sim: bool = Query(default=False)):
    try:
        session = await orchestrator.apply_short_loop_feedback(req, prefer_fast_sim=fast_sim)
        return session.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/debate/long-loop")
async def long_loop_decision(req: LongLoopDecisionRequest):
    try:
        result = orchestrator.apply_long_loop_decision(req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/baseline/compare")
async def compare_single_llm_baseline(req: StartDebateRequest, fast_sim: bool = Query(default=False)):
    """Runs each single LLM in isolation on the given scenario to compare with the Council."""
    options = req.candidate_options or [
        "NATS JetStream (Clustered Go Single-Binary) or Redpanda",
        "Apache Kafka on Kubernetes with Strimzi Operator (KRaft mode)",
        "Modular Monolith with Explicit Domain Boundaries & Single PostgreSQL",
    ]
    results = []
    for agent_cfg in orchestrator.get_agent_pool():
        if not agent_cfg.get("enabled", True):
            continue
        res = await SingleLLMBaseline.run_single_prompt(
            provider=agent_cfg["provider"],
            model=agent_cfg["model"],
            llm_family=agent_cfg["llm_family"],
            prompt=req.requirements_prompt,
            candidate_options=options,
            prefer_fast_sim=fast_sim,
        )
        results.append(res)
    return {"single_llm_baselines": results}


@app.post("/api/evaluate/experiment-a")
async def run_exp_a(fast_sim: bool = Query(default=True)):
    return await evaluation_engine.run_experiment_a(use_fast_sim=fast_sim)


@app.post("/api/evaluate/experiment-b")
async def run_exp_b(fast_sim: bool = Query(default=True)):
    return await evaluation_engine.run_experiment_b(use_fast_sim=fast_sim)


@app.get("/api/docs/list")
async def list_project_docs():
    docs = []
    guida_file = BASE_DIR / "GUIDA_COMPLETA_PROGETTO.md"
    arch_file = settings.DOCS_DIR / "ARCHITECTURE.md"
    eval_file = settings.DOCS_DIR / "EVALUATION_REPORT.md"
    if guida_file.exists():
        docs.append({"id": "GUIDA_COMPLETA", "title": "🇮🇹 Guida Completa & Tutorial Sito (Passo-Passo)", "content": guida_file.read_text(encoding="utf-8")})
    if arch_file.exists():
        docs.append({"id": "ARCHITECTURE", "title": "Software Architecture Document", "content": arch_file.read_text(encoding="utf-8")})
    if eval_file.exists():
        docs.append({"id": "EVALUATION_REPORT", "title": "Experimental Evaluation Report (Exp A & B)", "content": eval_file.read_text(encoding="utf-8")})
    adr_dir = settings.DOCS_DIR / "adr"
    if adr_dir.exists():
        for p in sorted(adr_dir.glob("*.md")):
            docs.append({"id": p.stem, "title": p.stem.replace("-", " "), "content": p.read_text(encoding="utf-8")})
    return {"docs": docs}


@app.get("/api/stream")
async def sse_stream():
    """Server-Sent Events endpoint streaming live A2A messages and phase updates."""
    q = message_bus.subscribe()

    async def event_generator():
        try:
            yield f"data: {json.dumps({'event': 'connected'})}\n\n"
            while True:
                try:
                    item = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(item)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            message_bus.unsubscribe(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/slides")
async def serve_professor_slides():
    slides_path = BASE_DIR / "architect-agent-project (2).html"
    if slides_path.exists():
        return FileResponse(slides_path)
    raise HTTPException(status_code=404, detail="Slides file not found")


@app.get("/defense")
async def serve_defense_slides():
    defense_path = settings.DOCS_DIR / "defense_presentation.html"
    if defense_path.exists():
        return FileResponse(defense_path)
    raise HTTPException(status_code=404, detail="Defense slides not found")


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")

