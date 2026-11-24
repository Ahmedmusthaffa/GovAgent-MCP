import os
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent_graph import GovernedLangGraphAgent

# Initialize FastAPI Application
app = FastAPI(
    title="GovAgent MCP - Enterprise Governed Agentic AI Platform",
    description="Model Context Protocol (MCP) tool-calling agent with Unity Catalog security governance and LangGraph state orchestration.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Agent Engine
agent_engine = GovernedLangGraphAgent()
APP_START_TIME = time.time()


# Request / Response Schemas
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User instruction or business question")
    role: str = Field("intern", description="Simulated user role: 'intern', 'manager', 'admin'")


class ChatResponse(BaseModel):
    user_query: str
    user_role: str
    final_response: str
    step_history: List[str]
    tool_events: List[Dict[str, Any]]
    governance_alerts: List[str]
    total_latency_ms: float


# API Routes
@app.get("/health")
def health_check():
    """Health check reporting system uptime, active MCP tools, and governance status."""
    return {
        "status": "healthy",
        "system": "GovAgent MCP Enterprise Platform",
        "uptime_seconds": round(time.time() - APP_START_TIME, 2),
        "governance_engine": "Unity Catalog Security Gate (Active)",
        "registered_mcp_tools": [
            "mcp_database_query (SQLite)",
            "mcp_vector_search (Enterprise SOPs)",
            "mcp_execute_refund (Business Operations)"
        ],
        "total_audit_events": len(agent_engine.security_gate.in_memory_audit_logs)
    }


@app.get("/api/v1/tools")
def get_available_mcp_tools():
    """Returns the list of registered MCP tools and their permission tiers."""
    return {
        "tools": [
            {
                "name": "mcp_database_query",
                "description": "Executes governed SQL queries against company database.",
                "governance_tier": "TIER 1 (Public) & TIER 3 (Restricted Salaries)",
                "rbac_policy": "Interns restricted to public tables with PII masking; Managers have full access."
            },
            {
                "name": "mcp_vector_search",
                "description": "Performs semantic vector search across company policies and SLA terms.",
                "governance_tier": "TIER 1 (Internal Documentation)",
                "rbac_policy": "Open to all employee roles."
            },
            {
                "name": "mcp_execute_refund",
                "description": "Dispatches customer resolutions and financial adjustments.",
                "governance_tier": "Financial Action Tool",
                "rbac_policy": "Interns capped at $500.00; Managers authorized up to $50,000.00."
            }
        ]
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
def execute_agent_chat(payload: ChatRequest):
    """
    Main Agentic Execution Endpoint.
    Routes the query through the LangGraph State Machine,
    executing MCP tools under Unity Catalog security enforcement.
    """
    result = agent_engine.run(user_query=payload.query, user_role=payload.role)
    return result


@app.get("/api/v1/audit/logs")
def get_compliance_audit_logs(limit: int = 20):
    """Retrieves immutable security audit logs for compliance auditing."""
    return {
        "audit_trail": agent_engine.security_gate.get_audit_trail(limit=limit)
    }


# Mount Static Frontend
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
