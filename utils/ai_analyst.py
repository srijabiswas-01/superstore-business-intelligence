"""Hybrid business analyst: deterministic Python answers plus grounded AI reports.

Python owns calculation and high-confidence question routing.  The language
model receives compact evidence tables and is used only for interpretation and
communication.  This separation reduces hallucination and keeps answers
auditable under the dashboard's active filters.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from utils.analytics import (
    build_business_context,
    build_dimension_summary,
    build_kpi_summary,
    build_product_summary,
    build_yearly_summary,
    context_to_text,
    validate_analysis_data,
)
from utils.insight_engine import build_inventory_report, is_inventory_question

try:
    from google import genai
except ImportError:  # The local Python analytics remain available without Gemini.
    genai = None


def _secret_or_env(secret_name: str, env_name: str, default: str = "") -> str:
    """Read optional Streamlit configuration without failing outside Streamlit."""
    try:
        value = st.secrets.get(secret_name, "")
        if value:
            return str(value)
    except (FileNotFoundError, KeyError):
        pass
    return os.getenv(env_name, default)


def get_api_key() -> str:
    """Return the Gemini API key from Streamlit secrets or the environment."""
    return _secret_or_env("GEMINI_API_KEY", "GEMINI_API_KEY")


def get_model_name() -> str:
    """Return the configured model so deployments can upgrade without code edits."""
    configured = _secret_or_env("GEMINI_MODEL", "GEMINI_MODEL")
    if configured:
        return configured
    # Support the project's original lowercase setting during migration.
    return _secret_or_env("model", "GEMINI_MODEL", "gemini-2.5-flash")


# Backward-compatible aliases used by existing pages and external notebooks.
build_kpi_context = build_kpi_summary
build_yearly_context = build_yearly_summary
dimension_summary = build_dimension_summary
build_product_context = build_product_summary


def build_discount_context(df: pd.DataFrame) -> pd.DataFrame:
    """Compatibility wrapper for the consolidated analytics module."""
    from utils.analytics import build_discount_summary
    return build_discount_summary(df)


def _single_result_report(answer: str, evidence: str, action: str) -> str:
    """Format deterministic answers consistently with AI-generated reports."""
    return (
        f"### Direct Answer\n{answer}\n\n"
        f"### Python-Verified Evidence\n{evidence}\n\n"
        "### Data Limitations\nThis conclusion uses only the currently filtered "
        "Superstore transactions.\n\n"
        f"### Recommended Action\n{action}"
    )


def answer_locally(question: str, df: pd.DataFrame) -> str | None:
    """Answer common factual and inventory questions entirely with Python."""
    validate_analysis_data(df)
    q = question.casefold().strip()

    if is_inventory_question(q):
        return build_inventory_report(df)

    yearly = None
    if "year" in q:
        yearly = build_yearly_summary(df)

    if "year" in q and "sales growth" in q:
        valid = yearly.dropna(subset=["sales_growth_pct"])
        if valid.empty:
            return _single_result_report(
                "At least two years are required to calculate growth.",
                "The active filters contain fewer than two comparable annual periods.",
                "Broaden the year filter before comparing annual growth.",
            )
        best = valid.loc[valid["sales_growth_pct"].idxmax()]
        return _single_result_report(
            f"{int(best['order_year'])} achieved the highest year-on-year sales growth.",
            f"Sales growth was **{best['sales_growth_pct']:.2f}%**.",
            "Review the products and regions responsible before treating the growth as repeatable.",
        )

    if "year" in q and "highest sales" in q:
        best = yearly.loc[yearly["sales"].idxmax()]
        return _single_result_report(
            f"{int(best['order_year'])} generated the highest annual sales.",
            f"Sales were **${best['sales']:,.2f}** across **{int(best['orders']):,} orders**.",
            "Use product and regional drill-downs to identify the repeatable contributors.",
        )

    if "year" in q and "highest profit" in q:
        best = yearly.loc[yearly["profit"].idxmax()]
        return _single_result_report(
            f"{int(best['order_year'])} generated the highest annual profit.",
            f"Profit was **${best['profit']:,.2f}**, with a **{best['profit_margin_pct']:.2f}%** margin.",
            "Compare its category mix and discount levels with weaker years.",
        )

    dimension_requests = (
        ("region", "region"), ("category", "category"),
        ("sub-category", "sub_category"), ("subcategory", "sub_category"),
        ("segment", "segment"),
    )
    for term, column in dimension_requests:
        if term not in q or not ("highest" in q or "most" in q):
            continue
        metric = "profit" if "profit" in q else "sales" if "sales" in q else None
        if metric:
            summary = build_dimension_summary(df, column)
            best = summary.loc[summary[metric].idxmax()]
            label = str(best[column])
            return _single_result_report(
                f"{label} generated the highest {metric} among {term} groups.",
                f"{metric.title()} was **${best[metric]:,.2f}**; profit margin was "
                f"**{best['profit_margin_pct']:.2f}%** across **{int(best['orders']):,} orders**.",
                "Validate whether performance remains consistent across time and lower-level groups.",
            )

    if "product" in q and ("highest profit" in q or "largest loss" in q or "worst" in q):
        products = build_product_summary(df)
        is_loss = "largest loss" in q or "worst" in q
        row = products.loc[products["profit"].idxmin() if is_loss else products["profit"].idxmax()]
        description = "largest product-level loss" if is_loss else "highest product-level profit"
        return _single_result_report(
            f"**{row['product_name']}** generated the {description}.",
            f"Profit was **${row['profit']:,.2f}** on **{int(row['quantity']):,} units** "
            f"across **{int(row['orders']):,} orders**, at a **{row['profit_margin_pct']:.2f}%** margin.",
            "Review demand frequency, discounting, and strategic importance before changing inventory or pricing.",
        )

    return None


def ask_ai(question: str, df: pd.DataFrame) -> str:
    """Ask Gemini to interpret only the Python-calculated evidence package."""
    if genai is None:
        raise RuntimeError("The Google GenAI SDK is not installed.")
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    evidence = context_to_text(build_business_context(df))
    prompt = f"""
ROLE
You are a careful senior business-intelligence analyst. Analyze only the
currently filtered Sample Superstore evidence supplied below.

USER QUESTION
{question}

PYTHON-VERIFIED EVIDENCE
{evidence}

GOVERNANCE RULES
1. Use only supplied evidence for factual claims and numbers.
2. Separate observed facts from interpretation and recommendations.
3. Never imply causation from correlation.
4. Do not rename sub-categories as categories.
5. Assess whether the evidence can actually answer the question. If important
   fields are absent, explicitly say the conclusion is provisional or that the
   evidence is insufficient.
6. Inventory advice requires stock on hand, stockouts, lead time, purchase cost,
   carrying cost, and service-level targets. Without them, call any ranking a
   demand-and-profit proxy, not a final allocation.
7. Do not equate high margin with high demand. Cite volume/order evidence when
   recommending operational priority.
8. Use full entity names exactly as shown in the evidence.
9. Be concise, decision-oriented, and avoid generic filler.
10. Answer only questions related to the supplied Superstore dataset or business
    decisions that can be evaluated from it. If a question is unrelated, state
    that this assistant is limited to the filtered Superstore business data.

REQUIRED RESPONSE FORMAT
### Direct Answer
Answer with an appropriate confidence qualifier.

### Python-Verified Evidence
List the strongest relevant facts and metrics.

### Business Interpretation
Explain what the facts suggest, without overstating them.

### Data Limitations
Name missing evidence that could materially change the conclusion. Write
"None material for this descriptive question" only when appropriate.

### Recommended Actions
Give numbered, measurable next steps tied to the evidence.
"""
    response = genai.Client(api_key=api_key).models.generate_content(
        model=get_model_name(), contents=prompt
    )
    if not getattr(response, "text", None):
        raise RuntimeError("The AI service returned an empty response.")
    return response.text.strip()


def ask_business_analyst(question: str, df: pd.DataFrame) -> dict[str, str]:
    """Route a question to deterministic Python or grounded AI interpretation."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Please enter a business question.")
    local_answer = answer_locally(question, df)
    if local_answer is not None:
        return {"mode": "Python Evidence", "answer": local_answer}
    return {"mode": "AI + Python Evidence", "answer": ask_ai(question, df)}
