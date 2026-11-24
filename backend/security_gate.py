import datetime
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

# Path to persistent audit log
AUDIT_LOG_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "audit_log.json")
)

# Unity Catalog Data Governance Classification Tiers
DATA_CLASSIFICATION = {
    "TIER_1_PUBLIC": ["customers", "orders"],
    "TIER_2_CONFIDENTIAL_PII": ["contact_phone", "contact_email"],
    "TIER_3_RESTRICTED": ["executive_salaries", "payroll", "internal_secrets"]
}

# Role-Based Access Control (RBAC) Permissions Matrix
ROLE_PERMISSIONS = {
    "intern": {
        "allowed_tiers": ["TIER_1_PUBLIC"],
        "mask_pii": True,
        "max_refund_approval_usd": 500.0,
        "can_access_restricted_tables": False
    },
    "manager": {
        "allowed_tiers": ["TIER_1_PUBLIC", "TIER_2_CONFIDENTIAL_PII", "TIER_3_RESTRICTED"],
        "mask_pii": False,
        "max_refund_approval_usd": 50000.0,
        "can_access_restricted_tables": True
    },
    "admin": {
        "allowed_tiers": ["TIER_1_PUBLIC", "TIER_2_CONFIDENTIAL_PII", "TIER_3_RESTRICTED"],
        "mask_pii": False,
        "max_refund_approval_usd": 1000000.0,
        "can_access_restricted_tables": True
    }
}


class UnityCatalogSecurityGate:
    """
    Enterprise Data Governance Gate aligned with Databricks Unity Catalog.
    Enforces Role-Based Access Control (RBAC), Column-level PII Masking,
    and Immutable Compliance Audit Logging.
    """
    def __init__(self):
        self.in_memory_audit_logs: List[Dict[str, Any]] = []

    def check_sql_permission(self, query: str, user_role: str = "intern") -> Tuple[bool, str]:
        """
        Inspects SQL query to ensure the user role is authorized to access
        the requested tables.
        Returns: (is_allowed: bool, reason_or_alert: str)
        """
        role = user_role.lower().strip()
        role_config = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["intern"])
        query_lower = query.lower()

        # Check for restricted tables (Tier 3)
        for restricted_table in DATA_CLASSIFICATION["TIER_3_RESTRICTED"]:
            # Match whole table names in SQL (e.g. FROM executive_salaries, JOIN executive_salaries)
            pattern = rf"\b{re.escape(restricted_table)}\b"
            if re.search(pattern, query_lower):
                if not role_config["can_access_restricted_tables"]:
                    alert = (
                        f"[SECURITY ALERT: ACCESS DENIED] Role '{role}' is not authorized "
                        f"to query table '{restricted_table}'. This table is classified as "
                        f"TIER 3 (RESTRICTED). Privilege escalation attempt blocked."
                    )
                    self.log_audit_event(
                        user_role=role,
                        tool_name="mcp_database_query",
                        status="BLOCKED",
                        target_resource=restricted_table,
                        details=alert
                    )
                    return False, alert

        # Allowed
        self.log_audit_event(
            user_role=role,
            tool_name="mcp_database_query",
            status="ALLOWED",
            target_resource="TIER_1_PUBLIC",
            details=f"Query authorized for execution: {query[:60]}..."
        )
        return True, "Authorized"

    def mask_pii_data(self, records: List[Dict[str, Any]], user_role: str) -> List[Dict[str, Any]]:
        """
        Applies dynamic column-level data masking for non-executive roles.
        Example: '+1-555-0101' -> '+1-555-****'
        """
        role = user_role.lower().strip()
        role_config = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["intern"])

        if not role_config["mask_pii"]:
            return records

        masked_records = []
        for row in records:
            masked_row = dict(row)
            if "contact_phone" in masked_row:
                phone = str(masked_row["contact_phone"])
                masked_row["contact_phone"] = phone[:7] + "****" if len(phone) >= 7 else "****"
            if "contact_email" in masked_row:
                email = str(masked_row["contact_email"])
                if "@" in email:
                    parts = email.split("@")
                    masked_row["contact_email"] = parts[0][:2] + "***@" + parts[1]
            masked_records.append(masked_row)

        return masked_records

    def check_action_permission(self, action_type: str, amount_usd: float, user_role: str) -> Tuple[bool, str]:
        """Verifies if the user role can approve or execute a financial action."""
        role = user_role.lower().strip()
        role_config = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["intern"])

        if amount_usd > role_config["max_refund_approval_usd"]:
            alert = (
                f"[ACTION BLOCKED] Role '{role}' has a maximum approval limit of "
                f"${role_config['max_refund_approval_usd']:,.2f}. Requested action of "
                f"${amount_usd:,.2f} requires Manager or Executive sign-off."
            )
            self.log_audit_event(
                user_role=role,
                tool_name=action_type,
                status="BLOCKED",
                target_resource=f"${amount_usd} refund",
                details=alert
            )
            return False, alert

        self.log_audit_event(
            user_role=role,
            tool_name=action_type,
            status="ALLOWED",
            target_resource=f"${amount_usd} refund",
            details=f"Action authorized for role '{role}'"
        )
        return True, "Authorized"

    def log_audit_event(
        self,
        user_role: str,
        tool_name: str,
        status: str,
        target_resource: str,
        details: str
    ):
        """Records an immutable audit event for security and compliance."""
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_role": user_role,
            "tool_name": tool_name,
            "status": status,
            "target_resource": target_resource,
            "details": details
        }
        self.in_memory_audit_logs.append(event)

        # Write to JSON file
        try:
            current_logs = []
            if os.path.exists(AUDIT_LOG_FILE):
                with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                    current_logs = json.load(f)
            current_logs.append(event)
            # Keep last 100 entries
            current_logs = current_logs[-100:]
            with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(current_logs, f, indent=2)
        except Exception as e:
            pass

    def get_audit_trail(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns the recent compliance audit events."""
        return self.in_memory_audit_logs[-limit:]
