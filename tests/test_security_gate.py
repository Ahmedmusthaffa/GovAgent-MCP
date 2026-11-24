import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from security_gate import UnityCatalogSecurityGate, ROLE_PERMISSIONS, DATA_CLASSIFICATION


class TestUnityCatalogSecurityGate(unittest.TestCase):
    def setUp(self):
        self.gate = UnityCatalogSecurityGate()

    def test_default_role_fallback(self):
        """Unrecognized roles should safely default to the intern (most restrictive) tier."""
        is_allowed, msg = self.gate.check_sql_permission("SELECT * FROM executive_salaries", user_role="unknown_guest")
        self.assertFalse(is_allowed)
        self.assertIn("SECURITY ALERT: ACCESS DENIED", msg)

    def test_intern_access_to_public_tables(self):
        """Intern should be permitted to query public customer tables."""
        is_allowed, msg = self.gate.check_sql_permission("SELECT customer_id, company_name FROM customers", user_role="intern")
        self.assertTrue(is_allowed)
        self.assertEqual(msg, "Authorized")

    def test_manager_access_to_restricted_tables(self):
        """Manager role should be authorized to query executive salaries."""
        is_allowed, msg = self.gate.check_sql_permission("SELECT * FROM executive_salaries", user_role="manager")
        self.assertTrue(is_allowed)
        self.assertEqual(msg, "Authorized")

    def test_admin_access_to_restricted_tables(self):
        """Admin role should also be authorized to query executive salaries."""
        is_allowed, msg = self.gate.check_sql_permission("SELECT * FROM executive_salaries", user_role="admin")
        self.assertTrue(is_allowed)
        self.assertEqual(msg, "Authorized")

    def test_pii_masking_intern(self):
        """Interns must see phone and email masked."""
        data = [
            {"customer_id": 1, "contact_phone": "+1-800-555-1234", "contact_email": "john.doe@enterprise.com"},
            {"customer_id": 2, "contact_phone": "123", "contact_email": "short@x.com"}
        ]
        masked = self.gate.mask_pii_data(data, user_role="intern")
        self.assertTrue(masked[0]["contact_phone"].endswith("****"))
        self.assertIn("***@", masked[0]["contact_email"])

    def test_pii_masking_manager_unmasked(self):
        """Managers should see original unmasked contact details."""
        data = [
            {"customer_id": 1, "contact_phone": "+1-800-555-1234", "contact_email": "john.doe@enterprise.com"}
        ]
        res = self.gate.mask_pii_data(data, user_role="manager")
        self.assertEqual(res[0]["contact_phone"], "+1-800-555-1234")
        self.assertEqual(res[0]["contact_email"], "john.doe@enterprise.com")

    def test_action_permissions_boundaries(self):
        """Verifies boundary thresholds for intern and manager financial actions."""
        # Exactly $500 should pass for intern
        allowed_500, _ = self.gate.check_action_permission("mcp_execute_refund", 500.0, "intern")
        self.assertTrue(allowed_500)

        # $500.01 should be blocked for intern
        blocked_501, msg = self.gate.check_action_permission("mcp_execute_refund", 500.01, "intern")
        self.assertFalse(blocked_501)
        self.assertIn("ACTION BLOCKED", msg)

        # $50,000 should pass for manager
        allowed_mgr, _ = self.gate.check_action_permission("mcp_execute_refund", 50000.0, "manager")
        self.assertTrue(allowed_mgr)

        # $50,000.01 should be blocked for manager
        blocked_mgr, _ = self.gate.check_action_permission("mcp_execute_refund", 50000.01, "manager")
        self.assertFalse(blocked_mgr)

    def test_audit_trail_recorded(self):
        """Audit trail should record events with required metadata."""
        initial_count = len(self.gate.in_memory_audit_logs)
        self.gate.check_sql_permission("SELECT * FROM customers", "intern")
        self.assertEqual(len(self.gate.in_memory_audit_logs), initial_count + 1)
        latest = self.gate.get_audit_trail(1)[-1]
        self.assertEqual(latest["status"], "ALLOWED")
        self.assertEqual(latest["tool_name"], "mcp_database_query")


if __name__ == "__main__":
    unittest.main()
