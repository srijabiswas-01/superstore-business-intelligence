"""Evidence-driven business reports that do not require a language model."""

from __future__ import annotations

import pandas as pd

from utils.analytics import build_inventory_priority, build_seasonality_summary


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


def is_seasonality_question(question: str) -> bool:
    """Identify questions about recurring seasonal or monthly sales patterns."""
    normalized = question.casefold()
    return any(term in normalized for term in ("seasonal", "seasonality", "season"))


def build_seasonality_report(df: pd.DataFrame) -> str:
    """Explain sales seasonality using monthly patterns and yearly variability."""
    yearly, profile = build_seasonality_summary(df)
    if yearly.empty or profile.empty:
        return (
            "### Direct Answer\nThere is not enough monthly history to assess seasonality.\n\n"
            "### Data Limitations\nAt least one complete year of monthly observations is required."
        )

    first = yearly.iloc[0]
    last = yearly.iloc[-1]
    direction = "increased" if last["monthly_variation_pct"] > first["monthly_variation_pct"] else "decreased"
    strongest = profile.nlargest(3, "seasonal_index")
    strongest_text = ", ".join(
        f"{row['month']} ({row['seasonal_index']:.1f})"
        for _, row in strongest.iterrows()
    )
    yearly_lines = "\n".join(
        f"- **{int(row['year'])}:** monthly variation {row['monthly_variation_pct']:.1f}%; "
        f"peak month {row['peak_month']} with {_money(row['peak_month_sales'])} in sales."
        for _, row in yearly.iterrows()
    )

    return (
        "### Direct Answer\n"
        f"Monthly sales variation {direction} from {first['monthly_variation_pct']:.1f}% "
        f"in {int(first['year'])} to {last['monthly_variation_pct']:.1f}% in "
        f"{int(last['year'])}. The history also shows recurring calendar-month "
        "concentration, but four years are not enough to establish a durable "
        "long-term change in seasonality.\n\n"
        "### Python-Verified Evidence\n"
        f"The strongest average calendar months by seasonal index are {strongest_text}; "
        "100 represents an average month.\n"
        f"{yearly_lines}\n\n"
        "### Business Interpretation\n"
        "The data supports monthly seasonality analysis and indicates whether within-year "
        "variation changed historically. It does not prove that the pattern will persist.\n\n"
        "### Data Limitations\n"
        "Only four annual cycles are available, and the dataset contains no holidays, "
        "promotions, market conditions, or external demand drivers.\n\n"
        "### Recommended Actions\n"
        "1. Use the monthly seasonal profile as a planning baseline.\n"
        "2. Validate peak months against promotion and holiday calendars.\n"
        "3. Refresh the analysis as additional years become available."
    )
