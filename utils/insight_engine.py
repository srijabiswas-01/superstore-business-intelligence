"""Evidence-driven business reports that do not require a language model."""

from __future__ import annotations

import pandas as pd

from utils.analytics import build_inventory_priority


INVENTORY_LIMITATIONS = (
    "The dataset does not contain current stock, stockouts, supplier lead times, "
    "purchase costs, carrying costs, or target service levels. The ranking is a "
    "replenishment-priority proxy, not a final purchase order."
)


def _money(value: float) -> str:
    """Format a numeric business value as US-dollar display text."""
    return f"${value:,.2f}"


def build_inventory_report(df: pd.DataFrame, limit: int = 5) -> str:
    """Return an organized inventory recommendation grounded in demand and profit."""
    ranked = build_inventory_priority(df, limit=limit)
    if ranked.empty:
        return (
            "### Direct Answer\nNo products meet the minimum evidence threshold.\n\n"
            f"### Data Limitations\n{INVENTORY_LIMITATIONS}"
        )

    evidence_rows = []
    for index, row in ranked.iterrows():
        evidence_rows.append(
            f"{index + 1}. **{row['product_name']}** — "
            f"{int(row['quantity']):,} units, {int(row['orders']):,} orders, "
            f"{int(row['recent_90d_quantity']):,} units in the latest 90 days, "
            f"{_money(row['profit'])} profit, {row['profit_margin_pct']:.1f}% margin."
        )

    return (
        "### Direct Answer\n"
        "Prioritize availability for the products below based on a balanced proxy "
        "of demand, repeat orders, recent demand, and positive profit.\n\n"
        "### Python-Verified Evidence\n" + "\n".join(evidence_rows) + "\n\n"
        "### Business Interpretation\n"
        "High-profit but low-frequency products should receive safety-stock review, "
        "not automatically the largest unit allocation. Consistently demanded and "
        "profitable products are stronger replenishment candidates.\n\n"
        "### Data Limitations\n" + INVENTORY_LIMITATIONS + "\n\n"
        "### Recommended Actions\n"
        "1. Validate the shortlist against on-hand stock, lead time, and stockout data.\n"
        "2. Set reorder points from recent demand and supplier lead time.\n"
        "3. Restrict replenishment for persistently loss-making products until pricing "
        "and discount policy are reviewed."
    )


def is_inventory_question(question: str) -> bool:
    """Identify questions asking for inventory, stocking, or replenishment advice."""
    normalized = question.casefold()
    terms = ("inventory", "stock", "replenish", "reorder", "allocation")
    return any(term in normalized for term in terms)
