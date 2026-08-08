"""Regression tests for trusted analytics and organized business reports."""

import json
import unittest
from unittest.mock import patch

from utils.ai_analyst import (
    ask_ai,
    ask_business_analyst,
    is_complete_structured_report,
    normalize_report_markdown,
    render_structured_report,
)
from utils.analytics import (
    build_inventory_priority,
    build_kpi_summary,
    build_product_summary,
    build_seasonality_summary,
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
            text = json.dumps({
                "direct_answer": "Grounded response based on supplied evidence.",
                "evidence": [{"label": "Result", "finding": "Verified value."}],
                "interpretation": ["The result supports further review."],
                "limitations": ["Only supplied data was evaluated."],
                "actions": [{"action": "Review result", "rationale": "Validate it."}],
            })

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

        self.assertIn("### Direct Answer", answer)
        self.assertIn("Grounded response", answer)

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

    def test_report_normalizer_prevents_currency_math_rendering(self):
        """Currency markers must not be interpreted as Streamlit LaTeX blocks."""
        raw = (
            "**Direct Answer**\nProfit was -$8,879.97 on $11,099.96 sales.\n\n\n"
            "**Recommended Actions:**\nReview pricing."
        )
        formatted = normalize_report_markdown(raw)

        self.assertIn("### Direct Answer", formatted)
        self.assertIn("-USD 8,879.97", formatted)
        self.assertIn("USD 11,099.96", formatted)
        self.assertIn("### Recommended Actions", formatted)
        self.assertNotIn("$", formatted)
        self.assertNotIn("\n\n\n", formatted)

    def test_structured_ai_report_has_consistent_executive_format(self):
        """JSON model output should become concise, scannable Markdown."""
        raw = json.dumps({
            "direct_answer": "Losses are concentrated in discounted products.",
            "evidence": [
                {"label": "Discount risk", "finding": "Profit was -$125,006.78."}
            ],
            "interpretation": ["High discounts are associated with weaker margins."],
            "limitations": ["Product cost detail is unavailable."],
            "actions": [
                {"action": "Review discount approvals", "rationale": "Focus on loss bands."}
            ],
        })
        formatted = render_structured_report(raw)

        self.assertIn("### Direct Answer", formatted)
        self.assertIn("- **Discount risk:**", formatted)
        self.assertIn("-USD 125,006.78", formatted)
        self.assertIn("1. **Review discount approvals**", formatted)
        self.assertNotIn("$", formatted)

    def test_incomplete_ai_report_is_rejected(self):
        """A direct answer alone must not pass the professional report contract."""
        incomplete = json.dumps({"direct_answer": "Only one section was returned."})
        self.assertFalse(is_complete_structured_report(incomplete))

    def test_seasonality_summary_uses_monthly_history(self):
        """Seasonality evidence should cover every year and calendar month."""
        yearly, profile = build_seasonality_summary(self.df)

        self.assertEqual(len(yearly), self.df["order_year"].nunique())
        self.assertEqual(len(profile), 12)
        self.assertTrue(yearly["monthly_variation_pct"].ge(0).all())

    @patch("utils.ai_analyst.ask_ai")
    def test_seasonality_question_uses_python_monthly_evidence(self, mock_ask_ai):
        """Seasonality questions must not be rejected or delegated without evidence."""
        result = ask_business_analyst(
            "Are sales becoming more seasonal?",
            self.df,
        )

        self.assertEqual(result["mode"], "Python Evidence")
        self.assertIn("monthly sales variation", result["answer"].lower())
        self.assertIn("four years", result["answer"].lower())
        mock_ask_ai.assert_not_called()


if __name__ == "__main__":
    unittest.main()
