import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from agent_graph import GovernedLangGraphAgent


class TestAgentGraph(unittest.TestCase):
    def setUp(self):
        self.agent = GovernedLangGraphAgent()

    def test_agent_customer_query_intern(self):
        """Query for customer orders as intern should succeed with masked PII."""
        res = self.agent.run("Show me all customer accounts and contact info", user_role="intern")
        self.assertEqual(res["user_role"], "intern")
        self.assertEqual(len(res["governance_alerts"]), 0)
        self.assertTrue(len(res["step_history"]) >= 3)
        self.assertIn("Enterprise Intelligence Summary", res["final_response"])
        self.assertTrue(res["total_latency_ms"] >= 0)

    def test_agent_blocked_salary_intern(self):
        """Query for salaries as intern should generate governance alert and security block response."""
        res = self.agent.run("What are executive salaries and what does the CEO earn?", user_role="intern")
        self.assertEqual(res["user_role"], "intern")
        self.assertTrue(len(res["governance_alerts"]) > 0)
        self.assertIn("Access Restricted by Unity Catalog Security Gate", res["final_response"])

    def test_agent_allowed_salary_manager(self):
        """Query for salaries as manager should succeed with executive compensation data."""
        res = self.agent.run("Show executive salaries for payroll audit", user_role="manager")
        self.assertEqual(res["user_role"], "manager")
        self.assertEqual(len(res["governance_alerts"]), 0)
        self.assertIn("Database Records Found", res["final_response"])

    def test_agent_multi_tool_dispute_and_policy(self):
        """Dispute query should invoke both SQL database tool and vector search tool."""
        res = self.agent.run("Find disputed delayed orders and review the refund SLA policy", user_role="intern")
        self.assertTrue(len(res["tool_events"]) >= 2)
        tool_names = [t.get("tool") for t in res["tool_events"]]
        self.assertIn("mcp_database_query", tool_names)
        self.assertIn("mcp_vector_search", tool_names)
        self.assertIn("Applicable Company Policies", res["final_response"])

    def test_agent_action_execution_flow(self):
        """Action execution prompt should invoke actions tool."""
        res = self.agent.run("Please issue refund of $200 for delayed delivery", user_role="intern")
        tool_names = [t.get("tool") for t in res["tool_events"]]
        self.assertIn("mcp_execute_refund", tool_names)
        self.assertIn("Action Dispatched", res["final_response"])


if __name__ == "__main__":
    unittest.main()
