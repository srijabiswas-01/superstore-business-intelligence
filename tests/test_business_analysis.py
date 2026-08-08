"""Regression tests for trusted analytics and organized business reports."""

import unittest
from unittest.mock import patch

from utils.ai_analyst import ask_ai, ask_business_analyst
from utils.analytics import (
    build_inventory_priority,
    build_kpi_summary,
    build_product_summary,
)
from utils.data_loader import load_processed_data


class BusinessAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = load_processed_data()

    def test_kpis_reconcile_to_source_data(self):
        kpis = build_kpi_summary(self.df).iloc[0]
        self.assertAlmostEqual(kpis["total_sales"], self.df["sales"].sum())
        self.assertAlmostEqual(kpis["total_profit"], self.df["profit"].sum())
        self.assertEqual(kpis["orders"], self.df["order_id"].nunique())

    def test_product_summary_contains_demand_and_profit_evidence(self):
        products = build_product_summary(self.df)
        expected = {
            "quantity", "orders", "profit", "profit_margin_pct",
            "recent_90d_quantity", "days_since_last_order",
        }
        self.assertTrue(expected.issubset(products.columns))

    def test_inventory_candidates_are_repeat_and_profitable(self):
        priorities = build_inventory_priority(self.df)
        self.assertFalse(priorities.empty)
        self.assertTrue(priorities["profit"].gt(0).all())
        self.assertTrue(priorities["orders"].ge(2).all())
        self.assertTrue(priorities["inventory_priority_score"].between(0, 100).all())

    def test_inventory_question_returns_governed_python_report(self):
        result = ask_business_analyst(
            "Which products should receive priority inventory allocation?",
            self.df,
        )
        self.assertEqual(result["mode"], "Python Evidence")
        for heading in (
            "### Direct Answer", "### Python-Verified Evidence",
            "### Business Interpretation", "### Data Limitations",
            "### Recommended Actions",
        ):
            self.assertIn(heading, result["answer"])
        self.assertIn("proxy", result["answer"].lower())
        self.assertIn("lead time", result["answer"].lower())

    def test_ai_client_stays_referenced_during_generation(self):
        """Ensure the cloud request uses a live client through response creation."""
        class FakeResponse:
            text = "Grounded response"

        class FakeModels:
            def generate_content(self, **kwargs):
                self.request = kwargs
                return FakeResponse()

        class FakeClient:
            def __init__(self, api_key):
                self.api_key = api_key
                self.models = FakeModels()

        class FakeGenAI:
            Client = FakeClient

        with (
            patch("utils.ai_analyst.genai", FakeGenAI),
            patch("utils.ai_analyst.get_api_key", return_value="test-key"),
            patch("utils.ai_analyst.get_model_name", return_value="test-model"),
        ):
            answer = ask_ai("Summarize performance", self.df)

        self.assertEqual(answer, "Grounded response")

    @patch("utils.ai_analyst.ask_ai")
    def test_unrelated_command_is_rejected_without_ai_call(self, mock_ask_ai):
        """Development commands should stop at the local scope guard."""
        result = ask_business_analyst("git push", self.df)

        self.assertEqual(result["mode"], "Scope Guard")
        self.assertNotIn("Python-Verified Evidence", result["answer"])
        mock_ask_ai.assert_not_called()

    @patch("utils.ai_analyst.ask_ai", return_value="Relevant analysis")
    def test_open_business_question_passes_scope_guard(self, mock_ask_ai):
        """Open-ended dataset questions must still reach grounded AI analysis."""
        result = ask_business_analyst(
            "What should management do about weak performance in the West?",
            self.df,
        )

        self.assertEqual(result["mode"], "AI + Python Evidence")
        self.assertEqual(result["answer"], "Relevant analysis")
        mock_ask_ai.assert_called_once()

    @patch("utils.ai_analyst.ask_ai", return_value="Discount scenario analysis")
    def test_plural_discount_question_passes_scope_guard(self, mock_ask_ai):
        """Plural business vocabulary must be recognized as dataset-related."""
        result = ask_business_analyst(
            "What will happen if discounts increase by 10%?",
            self.df,
        )

        self.assertEqual(result["mode"], "AI + Python Evidence")
        self.assertEqual(result["answer"], "Discount scenario analysis")
        mock_ask_ai.assert_called_once()


if __name__ == "__main__":
    unittest.main()
