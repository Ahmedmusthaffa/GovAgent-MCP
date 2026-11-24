import re
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from security_gate import UnityCatalogSecurityGate
from mcp_tools.database_tool import GovernedDatabaseTool
from mcp_tools.vector_tool import EnterpriseVectorSearchTool
from mcp_tools.actions_tool import GovernedActionsTool


class AgentState(BaseModel):
    user_query: str
    user_role: str = "intern"
    step_history: List[str] = Field(default_factory=list)
    tool_events: List[Dict[str, Any]] = Field(default_factory=list)
    governance_alerts: List[str] = Field(default_factory=list)
    retrieved_context: Dict[str, Any] = Field(default_factory=dict)
    final_response: str = ""
    total_latency_ms: float = 0.0


class GovernedLangGraphAgent:
    """
    LangGraph-inspired State Machine Agent.
    Orchestrates cyclical multi-tool execution across MCP tool servers
    with strict Unity Catalog security enforcement.
    """
    def __init__(self):
        self.security_gate = UnityCatalogSecurityGate()
        self.db_tool = GovernedDatabaseTool(self.security_gate)
        self.vector_tool = EnterpriseVectorSearchTool()
        self.actions_tool = GovernedActionsTool(self.security_gate)

    def run(self, user_query: str, user_role: str = "intern") -> Dict[str, Any]:
        """
        Executes the LangGraph State Machine pipeline:
        Plan -> Route & Call MCP Tools -> Verify Governance -> Synthesize Output.
        """
        start_time = time.time()
        role = user_role.lower().strip()
        state = AgentState(user_query=user_query, user_role=role)
        query_lower = user_query.lower()

        # Step 1: Planning Node (Analyze Intent)
        state.step_history.append("Node [1/3]: Analyzing query intent and security profile.")
        needs_sql = any(w in query_lower for w in ["order", "customer", "salary", "salaries", "revenue", "database", "who", "show", "list", "dispute", "delayed"])
        needs_vector = any(w in query_lower for w in ["policy", "rule", "sla", "refund", "guideline", "limit", "terms", "qualify", "can we"])
        needs_action = any(w in query_lower for w in ["issue refund", "send refund", "process refund", "dispatch email", "approve"])

        # Step 2: Tool Execution Node (Governed MCP Tool Calling)
        state.step_history.append("Node [2/3]: Routing to governed MCP tool servers.")

        # --- A. Check for SQL Tool Calling ---
        if needs_sql:
            # Dynamically determine target SQL query
            if "salary" in query_lower or "salaries" in query_lower or "ceo" in query_lower:
                sql = "SELECT full_name, job_title, annual_salary_usd FROM executive_salaries;"
            elif "dispute" in query_lower or "refund" in query_lower or "delayed" in query_lower:
                sql = "SELECT o.order_id, c.company_name, c.contact_phone, o.order_amount, o.status FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.status LIKE '%Disputed%' OR o.status LIKE '%Delayed%';"
            elif "customer" in query_lower:
                sql = "SELECT customer_id, company_name, contact_email, contact_phone, account_tier FROM customers;"
            else:
                sql = "SELECT order_id, customer_id, order_amount, status FROM orders;"

            db_res = self.db_tool.execute_query(sql, role)
            state.tool_events.append(db_res)
            state.retrieved_context["database"] = db_res

            if db_res["status"] == "BLOCKED":
                state.governance_alerts.append(db_res["security_alert"])

        # --- B. Check for Vector Search Tool Calling ---
        if needs_vector or "dispute" in query_lower or "refund" in query_lower:
            vector_res = self.vector_tool.search_policies(user_query, top_k=2)
            state.tool_events.append(vector_res)
            state.retrieved_context["policies"] = vector_res

        # --- C. Check for Action Execution Tool Calling ---
        if needs_action:
            # Check for refund action
            amount_match = re.search(r"\$?(\d+(?:\.\d+)?)", user_query)
            amount = float(amount_match.group(1)) if amount_match else 420.0
            
            action_res = self.actions_tool.process_refund_or_notice(
                customer_id=2,
                order_id=102,
                refund_amount_usd=amount,
                resolution_note="Automated dispute resolution initiated by user.",
                user_role=role
            )
            state.tool_events.append(action_res)
            state.retrieved_context["action"] = action_res

            if action_res["status"] == "BLOCKED":
                state.governance_alerts.append(action_res["security_alert"])

        # Step 3: Synthesis Node (Human-Readable Executive Response)
        state.step_history.append("Node [3/3]: Synthesizing governed response.")
        total_time = round((time.time() - start_time) * 1000, 2)
        state.total_latency_ms = total_time

        final_text = self._synthesize_answer(state)
        state.final_response = final_text

        return state.model_dump()

    def _synthesize_answer(self, state: AgentState) -> str:
        """Constructs an articulate response highlighting findings and security enforcement."""
        # 1. If security blocked the request
        if state.governance_alerts:
            alerts_text = "\n".join([f"⚠️ {alert}" for alert in state.governance_alerts])
            return (
                f"### 🛡️ Access Restricted by Unity Catalog Security Gate\n\n"
                f"{alerts_text}\n\n"
                f"**Audit Note:** Your access attempt has been logged into the compliance audit trail under role `{state.user_role}`. "
                f"If you require access to privileged datasets, please request elevated permissions from your system administrator."
            )

        # 2. If data and policies were retrieved successfully
        parts = []
        parts.append(f"### 📋 Enterprise Intelligence Summary (Role: {state.user_role.capitalize()})\n")

        # Database Findings
        db_data = state.retrieved_context.get("database")
        if db_data and db_data.get("rows"):
            rows = db_data["rows"]
            parts.append(f"**Database Records Found ({len(rows)} matching entries):**")
            for r in rows:
                row_str = ", ".join([f"**{k}**: {v}" for k, v in r.items()])
                parts.append(f"- {row_str}")
            parts.append("")

        # Policy Findings
        policy_data = state.retrieved_context.get("policies")
        if policy_data and policy_data.get("results"):
            parts.append("**Applicable Company Policies (Vector Search):**")
            for res in policy_data["results"]:
                parts.append(f"> *From `{res['doc_name']}` (Relevance: {res['relevance_score']}%):*\n> \"{res['text']}\"\n")

        # Action Findings
        action_data = state.retrieved_context.get("action")
        if action_data and action_data.get("status") == "EXECUTED":
            parts.append(
                f"**Action Dispatched:** Successfully processed resolution of "
                f"**${action_data['amount_usd']:,.2f}** for Customer #{action_data['customer_id']} "
                f"(Order #{action_data['order_id']})."
            )

        if len(parts) == 1:
            return (
                f"Hello! I am your Enterprise Governed AI Assistant. "
                f"You are currently logged in with role: `{state.user_role}`. "
                f"You can ask me to search customer orders, company policies, or review refund resolutions."
            )

        return "\n".join(parts)
