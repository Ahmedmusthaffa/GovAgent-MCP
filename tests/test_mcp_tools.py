import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from security_gate import UnityCatalogSecurityGate
from mcp_tools.database_tool import GovernedDatabaseTool
from mcp_tools.vector_tool import EnterpriseVectorSearchTool
from mcp_tools.actions_tool import GovernedActionsTool


class TestMcpTools(unittest.TestCase):
    def setUp(self):
        self.gate = UnityCatalogSecurityGate()
        self.db_tool = GovernedDatabaseTool(self.gate)
        self.vector_tool = EnterpriseVectorSearchTool()
        self.actions_tool = GovernedActionsTool(self.gate)

    def test_database_tool_allowed_query(self):
        """Database tool should return results for allowed tables with masked PII for intern."""
        res = self.db_tool.execute_query("SELECT customer_id, company_name, contact_phone FROM customers LIMIT 2;", user_role="intern")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["tool"], "mcp_database_query")
        self.assertTrue(len(res["rows"]) > 0)
        # Check PII masking
        self.assertTrue(res["rows"][0]["contact_phone"].endswith("****"))

    def test_database_tool_blocked_query(self):
        """Database tool should block restricted tables for intern."""
        res = self.db_tool.execute_query("SELECT * FROM executive_salaries;", user_role="intern")
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("SECURITY ALERT: ACCESS DENIED", res["security_alert"])
        self.assertEqual(len(res["rows"]), 0)

    def test_database_tool_manager_access(self):
        """Database tool should permit manager to query executive salaries."""
        res = self.db_tool.execute_query("SELECT full_name, annual_salary_usd FROM executive_salaries;", user_role="manager")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(len(res["rows"]) > 0)

    def test_vector_search_tool_retrieval(self):
        """Vector search should retrieve policy clauses relevant to refund."""
        res = self.vector_tool.search_policies("What is the refund limit and SLA policy for delayed orders?", top_k=2)
        self.assertEqual(res["tool"], "mcp_vector_search")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(len(res["results"]) > 0)
        self.assertTrue(res["results"][0]["relevance_score"] > 50)
        self.assertIn("refund", res["results"][0]["text"].lower())

    def test_actions_tool_intern_approved_refund(self):
        """Actions tool executes refund below intern limit."""
        res = self.actions_tool.process_refund_or_notice(
            customer_id=1,
            order_id=101,
            refund_amount_usd=250.0,
            resolution_note="Customer delay compensation",
            user_role="intern"
        )
        self.assertEqual(res["status"], "EXECUTED")
        self.assertEqual(res["amount_usd"], 250.0)

    def test_actions_tool_intern_blocked_refund(self):
        """Actions tool blocks refund exceeding intern limit."""
        res = self.actions_tool.process_refund_or_notice(
            customer_id=1,
            order_id=101,
            refund_amount_usd=900.0,
            resolution_note="Large order compensation",
            user_role="intern"
        )
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("ACTION BLOCKED", res["security_alert"])


if __name__ == "__main__":
    unittest.main()
