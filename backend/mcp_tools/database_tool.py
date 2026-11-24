import os
import sqlite3
import time
from typing import Any, Dict, List

# Path to SQLite company database
DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "company.db")
)


class GovernedDatabaseTool:
    """
    Model Context Protocol (MCP) compliant Database Tool.
    Safely queries enterprise SQLite tables under Unity Catalog governance.
    """
    def __init__(self, security_gate):
        self.security_gate = security_gate

    def execute_query(self, query: str, user_role: str = "intern") -> Dict[str, Any]:
        """
        Executes SQL query if approved by the Unity Catalog Security Gate.
        Applies automatic column PII masking for non-executive roles.
        """
        start_time = time.time()

        # Step 1: Security Inspection
        is_allowed, reason = self.security_gate.check_sql_permission(query, user_role)
        if not is_allowed:
            return {
                "tool": "mcp_database_query",
                "status": "BLOCKED",
                "security_alert": reason,
                "rows": [],
                "row_count": 0,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2)
            }

        # Step 2: Governed SQL Execution
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            raw_rows = cursor.fetchall()
            
            # Convert rows to standard dicts
            dict_rows = [dict(row) for row in raw_rows]
            conn.close()

            # Step 3: Column-level PII Masking
            masked_rows = self.security_gate.mask_pii_data(dict_rows, user_role)

            return {
                "tool": "mcp_database_query",
                "status": "SUCCESS",
                "security_clearance": f"Approved for role '{user_role}'",
                "rows": masked_rows,
                "row_count": len(masked_rows),
                "execution_time_ms": round((time.time() - start_time) * 1000, 2)
            }

        except Exception as e:
            return {
                "tool": "mcp_database_query",
                "status": "SQL_ERROR",
                "error": str(e),
                "rows": [],
                "row_count": 0,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2)
            }
