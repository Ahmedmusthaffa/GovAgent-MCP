# GovAgent MCP: Enterprise Governed Agentic AI Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/Model_Context_Protocol-Enterprise_Standard-2563EB?style=flat)](https://modelcontextprotocol.io/)
[![Unity Catalog](https://img.shields.io/badge/Governance-Databricks_Unity_Catalog-FF3621?style=flat)](https://www.databricks.com/product/unity-catalog)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph_State_Machine-0F172A?style=flat)](https://www.langchain.com/langgraph)
[![Tests Passing](https://img.shields.io/badge/Tests-24%2F24_Passing-059669?style=flat)]()

**GovAgent MCP** is an enterprise-grade agentic AI platform designed to securely connect Large Language Models with external corporate databases, unstructured policy documents, and business operations workflows.

Built on the **Model Context Protocol (MCP)**, **Databricks Unity Catalog governance principles**, and **LangGraph state machine orchestration**, GovAgent solves the critical security and governance challenges blocking enterprise AI deployment: **unauthorized privilege escalation**, **PII data leakage**, and **uncontrolled financial actions**.

---

## 📸 Platform Previews

### 1. Privilege Escalation Defense (Access Restricted)
When an `intern` attempts to query restricted executive salaries, the Unity Catalog Security Gate intercepts the query, halts execution, alerts the user, and logs an immutable compliance audit event.

![Security Block Preview](docs/images/govagent_security_block.png)

### 2. Multi-Tool Orchestration with Dynamic PII Masking
When queried about delayed orders and refund policies, the LangGraph engine orchestrates parallel MCP tool calls across SQLite databases (with phone/email PII masking applied) and semantic vector search over company SOPs.

![Multi-Tool Preview](docs/images/govagent_multi_tool.png)

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User([Corporate User: Intern / Manager / Admin]) -->|Natural Language Prompt| UI[Human-Crafted Web UI]
    UI -->|REST API /api/v1/chat| Gateway[FastAPI Enterprise Gateway]
    
    subgraph Agentic Orchestration [LangGraph State Machine]
        Gateway --> Node1[Node 1: Intent & Security Profiler]
        Node1 --> Node2[Node 2: Governed MCP Router]
        Node2 --> Node3[Node 3: Response Synthesis & Evidence Linking]
    end

    subgraph Governance Core [Databricks Unity Catalog Security Gate]
        Node2 --> Gate{Unity Catalog Policy Engine}
        Gate -->|RBAC Matrix| RBAC[Tier 1 / Tier 2 / Tier 3 Clearance]
        Gate -->|Column Inspection| PII[Dynamic PII Masking Engine]
        Gate -->|Action Limits| LimitCheck[Financial Threshold Guard: $500 Intern / $50k Mgr]
        Gate -->|Every Operation| AuditLog[(Immutable Audit Trail JSON/DB)]
    end

    subgraph MCP Tool Ecosystem [Model Context Protocol Servers]
        Gate -->|Authorized SQL| MCP_DB[mcp_database_query SQLite DB]
        Gate -->|Vector Retrieval| MCP_VEC[mcp_vector_search Enterprise SOPs]
        Gate -->|Approved Actions| MCP_ACT[mcp_execute_refund Financial Ops]
    end

    MCP_DB --> Node3
    MCP_VEC --> Node3
    MCP_ACT --> Node3
    Node3 --> Gateway
```

---

## ⚡ Key Architectural Capabilities

### 1. Databricks Unity Catalog 3-Tier Data Governance
Implements strict enterprise catalog segmentation:
- **TIER 1 (Public Datasets):** `customers`, `orders` (Open to all employee roles).
- **TIER 2 (Confidential PII):** Customer telephone numbers and emails. Dynamically masked for non-managerial roles (`+1-555-****`, `op***@domain.com`).
- **TIER 3 (Restricted Datasets):** `executive_salaries`, `payroll`, `confidential_records`. Queries from unauthorized roles are intercepted with an instant `[SECURITY ALERT: ACCESS DENIED]` before reaching the database engine.

### 2. Model Context Protocol (MCP) Standardized Tools
- `mcp_database_query`: Governed enterprise database tool executing SQL under Unity Catalog permissions.
- `mcp_vector_search`: Semantic vector search engine matching user inquiries with policy clauses and SLA agreements.
- `mcp_execute_refund`: High-impact business operation tool that dispatches financial actions only after verifying role-based approval limits ($500 for interns, $50,000 for managers).

### 3. LangGraph Cyclical State Machine
Routes complex multi-part enterprise questions through a deterministic 3-node cycle:
1. **Planning Node:** Parses intent, extracts financial thresholds, evaluates role clearance.
2. **Tool Execution Node:** Dispatches parallel or sequential MCP tool calls with governance validation.
3. **Synthesis Node:** Merges database records, policy citations, and action confirmations into an executive-ready response.

### 4. Immutable Compliance & Audit Trail (SOC 2 / ISO 27001 Ready)
Every authorization check, blocked query, and executed action is logged with:
- ISO 8601 timestamp
- User role
- MCP tool name
- Access status (`ALLOWED` / `BLOCKED`)
- Resource target & security details

---

## 🛡️ Security Audit & Penetration Testing

GovAgent includes an automated security audit suite (`security/security_audit.py`) inspired by enterprise red-teaming standards:

| Penetration Test | Attack Scenario | Defense Mechanism | Result |
| :--- | :--- | :--- | :---: |
| **Privilege Escalation** | Intern attempts SQL query on `executive_salaries` | Unity Catalog table guard blocks query before DB execution | **PASSED** |
| **SQL Injection Bypass** | SQL injection string `WHERE 1=1 JOIN executive_salaries` | AST regex table inspection catches restricted table name | **PASSED** |
| **PII Data Leakage** | Non-executive role requests customer contacts | Column-level masking hashes phone & email | **PASSED** |
| **Over-Spend Action Violation** | Intern attempts to approve $1,500 refund | Hard threshold enforcement blocks amounts > $500.00 | **PASSED** |
| **Audit Trail Tampering** | Audit log verification | All events recorded to immutable append-only trail | **PASSED** |

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python 3.10+
- SQLite3

### 1. Clone the Repository
```bash
git clone https://github.com/Ahmedmusthaffa/GovAgent-MCP.git
cd GovAgent-MCP
```

### 2. Install Dependencies
```bash
pip install fastapi uvicorn pydantic httpx pytest
```

### 3. Seed Database & Policies
```bash
python data/seed_database.py
```

### 4. Run the Test Suites (100% Pass)
```bash
# Run Security Penetration Test Suite
python security/security_audit.py

# Run Full Unit & Integration Test Suite
python -m pytest tests/ -v
```

### 5. Launch the Enterprise Server
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

Open your browser at **`http://localhost:8001`** to interact with the dual-panel governance interface.

---

## 📡 REST API Documentation

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/health` | `GET` | Health status, active MCP tools, and uptime |
| `/api/v1/tools` | `GET` | Catalog of registered MCP tools and their permission tiers |
| `/api/v1/chat` | `POST` | Agent execution endpoint accepting `{ query, role }` |
| `/api/v1/audit/logs` | `GET` | Retrieves recent compliance audit events |

---

## 👨‍💻 Author

**Ahmed Musthaffa (Ahmed M)**  
- MCA Candidate (2024–2026), PMIST | BCA (2024)
- AWS Certified Cloud Practitioner
- Research Author: *IEEE ICIRCA 2024* (Edge-Deployed EEG Stress Detection)
- Portfolio: [ahmed-portfolio-kohl.vercel.app](https://ahmed-portfolio-kohl.vercel.app/)
- GitHub: [@Ahmedmusthaffa](https://github.com/Ahmedmusthaffa)
