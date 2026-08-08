"""Hybrid business analyst: deterministic Python answers plus grounded AI reports.

Python owns calculation and high-confidence question routing.  The language
model receives compact evidence tables and is used only for interpretation and
communication.  This separation reduces hallucination and keeps answers
auditable under the dashboard's active filters.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata

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


def normalize_report_markdown(answer: str) -> str:
    """Normalize model output for stable, readable Streamlit Markdown.

    Streamlit can interpret pairs of dollar signs as LaTeX math delimiters.
    Currency is therefore converted to an explicit ``USD`` prefix. Common
    heading variations are also converted to the report's canonical headings.
    """
    text = unicodedata.normalize("NFKC", str(answer)).strip()
    text = re.sub(r"-\s*\$\s*(?=\d)", "-USD ", text)
    text = re.sub(r"\$\s*(?=\d)", "USD ", text)

    headings = (
        "Direct Answer",
        "Python-Verified Evidence",
        "Business Interpretation",
        "Data Limitations",
        "Recommended Actions",
        "Recommended Action",
    )
    for heading in headings:
        pattern = (
            rf"(?im)^\s*(?:#{{1,6}}\s*)?(?:\*\*)?"
            rf"{re.escape(heading)}\s*:?(?:\*\*)?[ \t]*$"
        )
        text = re.sub(pattern, f"### {heading}", text)

    # Avoid excessive blank space from variable model formatting.
    return re.sub(r"\n{3,}", "\n\n", text)


def render_structured_report(raw_response: str) -> str:
    """Render a Gemini JSON report as consistent executive Markdown.

    Invalid or legacy non-JSON responses fall back to the Markdown normalizer,
    keeping deployments compatible while structured output propagates.
    """
    raw = str(raw_response).strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)

    try:
        report = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return normalize_report_markdown(raw)

    if not isinstance(report, dict) or not report.get("direct_answer"):
        return normalize_report_markdown(raw)

    def clean(value: object) -> str:
        return normalize_report_markdown(str(value)).replace("\n", " ").strip()

    sections = ["### Direct Answer", clean(report["direct_answer"])]

    evidence = report.get("evidence", [])
    if isinstance(evidence, list) and evidence:
        sections.append("### Python-Verified Evidence")
        rows = []
        for item in evidence[:5]:
            if isinstance(item, dict):
                label = clean(item.get("label", "Finding"))
                finding = clean(item.get("finding", ""))
                if finding:
                    rows.append(f"- **{label}:** {finding}")
        sections.append("\n".join(rows))

    interpretation = report.get("interpretation", [])
    if isinstance(interpretation, list) and interpretation:
        sections.extend([
            "### Business Interpretation",
            "\n".join(f"- {clean(item)}" for item in interpretation[:3]),
        ])

    limitations = report.get("limitations", [])
    if isinstance(limitations, list) and limitations:
        sections.extend([
            "### Data Limitations",
            "\n".join(f"- {clean(item)}" for item in limitations[:3]),
        ])

    actions = report.get("actions", [])
    if isinstance(actions, list) and actions:
        rows = []
        for number, item in enumerate(actions[:5], start=1):
            if isinstance(item, dict):
                action = clean(item.get("action", ""))
                rationale = clean(item.get("rationale", ""))
                if action:
                    detail = f" — {rationale}" if rationale else ""
                    rows.append(f"{number}. **{action}**{detail}")
            elif item:
                rows.append(f"{number}. {clean(item)}")
        sections.extend(["### Recommended Actions", "\n".join(rows)])

    return "\n\n".join(section for section in sections if section)


def is_dataset_question(question: str, df: pd.DataFrame) -> bool:
    """Return whether a question belongs to the Superstore analysis domain.

    Explicit development commands are rejected first. Other questions are
    accepted when they contain a business-analysis concept or reference a value
    from a major dataset dimension. This local gate prevents unrelated prompts
    from consuming an AI request or receiving a fabricated business report.
    """
    normalized = " ".join(question.casefold().split())
    if not normalized:
        return False

    technical_command = re.compile(
        r"^(git|pip|python|python3|npm|npx|yarn|docker|kubectl|terraform|"
        r"curl|wget|ssh|streamlit|powershell|bash)\b"
    )
    if technical_command.search(normalized):
        return False

    business_terms = {
        "sale", "sales", "revenue", "profit", "profitable", "profitability",
        "margin", "loss", "losses", "order", "orders", "customer", "customers",
        "product", "products", "category", "categories", "subcategory",
        "sub-category", "segment", "region", "state", "city", "market",
        "discount", "discounting", "price", "pricing", "quantity", "units",
        "shipping", "delivery", "delay", "ship mode", "inventory", "stock",
        "replenishment", "forecast", "forecasting", "growth", "trend", "risk",
        "performance", "opportunity", "opportunities", "management", "business",
        "priority", "priorities", "strategy", "operations", "year", "month",
        "quarter", "compare", "highest", "lowest", "best", "worst",
    }
    tokens = set(re.findall(r"[a-z0-9-]+", normalized))
    # Match simple plural forms such as discounts, regions, products, and
    # customers without forcing users to use the exact vocabulary in this set.
    tokens.update(
        token[:-1]
        for token in tuple(tokens)
        if len(token) > 3 and token.endswith("s")
    )
    if tokens.intersection(business_terms):
        return True

    # Accept references to actual filtered dimension values such as "West",
    # "Technology", or a named state, even when no explicit metric is supplied.
    for column in ("region", "category", "sub_category", "segment", "state", "city"):
        if column not in df.columns:
            continue
        values = df[column].dropna().astype(str).str.casefold().unique()
        if any(len(value) >= 3 and value in normalized for value in values):
            return True

    return False


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
9. Be concise, decision-oriented, and avoid generic filler or repeated metrics.
10. Answer only questions related to the supplied Superstore dataset or business
    decisions that can be evaluated from it. If a question is unrelated, state
    that this assistant is limited to the filtered Superstore business data.
11. Write currency as "USD 1,234.56" or "-USD 1,234.56". Never use dollar
    symbols, LaTeX, mathematical markup, or escaped equations.
12. Include no more than five evidence bullets and five recommended actions.
13. Do not invent numeric targets, thresholds, or policy limits. A number in a
    recommendation must come from the supplied evidence or be explicitly labeled
    as a proposed target requiring validation.
14. Display discount rates as percentages, never raw decimal ratios. For example,
    write 37.02%, not 0.3702.
15. Do not use confidence language for recommendations. Reserve certainty for
    directly calculated descriptive facts.
16. Distinguish "associated with" from causation and do not say an item should be
    discontinued when the evidence supports only review or investigation.

REQUIRED RESPONSE FORMAT
Return only valid JSON with this exact structure and no Markdown fences:
{{
  "direct_answer": "A focused answer of no more than three sentences.",
  "evidence": [
    {{"label": "Short label", "finding": "One verified finding with context."}}
  ],
  "interpretation": ["Two or three concise implications, without repeated figures."],
  "limitations": ["Only limitations material to this decision."],
  "actions": [
    {{"action": "Specific action", "rationale": "Why this follows from evidence."}}
  ]
}}
"""
    # Keep a strong reference to the client for the complete network request.
    # Creating it inline can allow the temporary client to be finalized early
    # in long-lived Streamlit runtimes, producing "client has been closed".
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=get_model_name(),
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    if not getattr(response, "text", None):
        raise RuntimeError("The AI service returned an empty response.")
    return render_structured_report(response.text)


def ask_business_analyst(question: str, df: pd.DataFrame) -> dict[str, str]:
    """Route a question to deterministic Python or grounded AI interpretation."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Please enter a business question.")
    if not is_dataset_question(question, df):
        return {
            "mode": "Scope Guard",
            "answer": (
                "This assistant only answers questions about the currently "
                "filtered Superstore business data. Ask about sales, profit, "
                "products, customers, regions, discounts, shipping, forecasting, "
                "inventory evidence, or management priorities."
            ),
        }
    local_answer = answer_locally(question, df)
    if local_answer is not None:
        return {
            "mode": "Python Evidence",
            "answer": normalize_report_markdown(local_answer),
        }
    return {
        "mode": "AI + Python Evidence",
        "answer": normalize_report_markdown(ask_ai(question, df)),
    }
