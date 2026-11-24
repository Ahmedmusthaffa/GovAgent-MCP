import time
from typing import Any, Dict


class GovernedActionsTool:
    """
    Model Context Protocol (MCP) compliant Operations & Action Dispatch Tool.
    Safely executes high-impact business workflows (e.g., refunds, email notices)
    only after Unity Catalog threshold verification.
    """
    def __init__(self, security_gate):
        self.security_gate = security_gate

    def process_refund_or_notice(
        self,
        customer_id: int,
        order_id: int,
        refund_amount_usd: float,
        resolution_note: str,
        user_role: str = "intern"
    ) -> Dict[str, Any]:
        """
        Executes customer resolution if within the user's role authorization limit.
        """
        start_time = time.time()

        # Step 1: Governance & Authorization Verification
        is_allowed, reason = self.security_gate.check_action_permission(
            action_type="mcp_execute_refund",
            amount_usd=refund_amount_usd,
            user_role=user_role
        )

        if not is_allowed:
            return {
                "tool": "mcp_execute_refund",
                "status": "BLOCKED",
                "security_alert": reason,
                "amount_usd": refund_amount_usd,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2)
            }

        # Step 2: Execute Action
        return {
            "tool": "mcp_execute_refund",
            "status": "EXECUTED",
            "security_clearance": f"Authorized for role '{user_role}'",
            "customer_id": customer_id,
            "order_id": order_id,
            "amount_usd": refund_amount_usd,
            "resolution_note": resolution_note,
            "dispatch_status": "Email notice queued and financial adjustment dispatched.",
            "execution_time_ms": round((time.time() - start_time) * 1000, 2)
        }
