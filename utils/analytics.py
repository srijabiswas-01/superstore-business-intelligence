"""Reusable, deterministic business aggregations.

All figures supplied to the AI layer are calculated here.  Keeping numerical
work outside the language-model prompt makes the results testable and prevents
the model from inventing metrics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


CORE_COLUMNS = {
    "sales", "profit", "quantity", "discount", "order_id", "customer_id",
    "order_date", "shipping_delay", "product_name",
}


def validate_analysis_data(df: pd.DataFrame) -> None:
    """Raise a helpful error when processed Superstore fields are unavailable."""
    missing = sorted(CORE_COLUMNS.difference(df.columns))
    if missing:
        raise ValueError(f"Analysis data is missing required columns: {', '.join(missing)}")
    if df.empty:
        raise ValueError("Analysis requires at least one transaction.")


def add_profit_margin(table: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with a safe aggregate profit-margin percentage."""
    result = table.copy()
    result["profit_margin_pct"] = np.where(
        result["sales"].ne(0), result["profit"].div(result["sales"]).mul(100), 0.0
    )
    return result


def build_kpi_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build a one-row executive KPI table for the active filter selection."""
    validate_analysis_data(df)
    sales = df["sales"].sum()
    profit = df["profit"].sum()
    return pd.DataFrame([{
        "total_sales": sales,
        "total_profit": profit,
        "profit_margin_pct": profit / sales * 100 if sales else 0.0,
        "orders": df["order_id"].nunique(),
        "customers": df["customer_id"].nunique(),
        "units": df["quantity"].sum(),
        "average_discount_pct": df["discount"].mean() * 100,
        "average_shipping_delay_days": df["shipping_delay"].mean(),
    }])


def build_yearly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate annual performance and calculate year-over-year changes."""
    yearly = (
        df.groupby("order_year", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"),
             quantity=("quantity", "sum"), orders=("order_id", "nunique"))
        .sort_values("order_year")
    )
    yearly["sales_growth_pct"] = yearly["sales"].pct_change() * 100
    yearly["profit_growth_pct"] = yearly["profit"].pct_change() * 100
    return add_profit_margin(yearly)


def build_dimension_summary(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Aggregate commercial and operational metrics for one dimension."""
    if dimension not in df.columns:
        raise ValueError(f"Unknown analysis dimension: {dimension}")
    result = df.groupby(dimension, observed=True, as_index=False).agg(
        sales=("sales", "sum"), profit=("profit", "sum"),
        quantity=("quantity", "sum"), orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        average_discount_pct=("discount", "mean"),
        shipping_delay=("shipping_delay", "mean"),
    )
    result["average_discount_pct"] *= 100
    return add_profit_margin(result)


def build_product_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate product profitability, demand, frequency, and recent demand."""
    validate_analysis_data(df)
    latest_date = df["order_date"].max()
    recent_start = latest_date - pd.Timedelta(days=90)
    recent = (
        df.loc[df["order_date"].ge(recent_start)]
        .groupby("product_name", observed=True)["quantity"].sum()
        .rename("recent_90d_quantity")
    )
    product = df.groupby("product_name", observed=True, as_index=False).agg(
        sales=("sales", "sum"), profit=("profit", "sum"),
        quantity=("quantity", "sum"), orders=("order_id", "nunique"),
        average_discount_pct=("discount", "mean"),
        last_order_date=("order_date", "max"),
    )
    product["average_discount_pct"] *= 100
    product = product.join(recent, on="product_name").fillna({"recent_90d_quantity": 0})
    product["days_since_last_order"] = (latest_date - product["last_order_date"]).dt.days
    return add_profit_margin(product)


def build_discount_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize outcomes for the engineered discount bands."""
    result = df.groupby("discount_band", observed=True, as_index=False).agg(
        sales=("sales", "sum"), profit=("profit", "sum"),
        quantity=("quantity", "sum"), orders=("order_id", "nunique"),
    )
    return add_profit_margin(result)


def build_inventory_priority(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """Rank replenishment candidates using a transparent profitability proxy.

    This is not an inventory optimization model: the source data has no stock,
    lead-time, service-level, or carrying-cost fields.  The score balances unit
    demand, order frequency, recent demand, and profit, and excludes products
    without positive aggregate profit or repeat orders.
    """
    products = build_product_summary(df)
    eligible = products.loc[(products["profit"] > 0) & (products["orders"] >= 2)].copy()
    if eligible.empty:
        return eligible.assign(inventory_priority_score=pd.Series(dtype=float))

    score_inputs = {
        "quantity": 0.30,
        "orders": 0.25,
        "recent_90d_quantity": 0.20,
        "profit": 0.25,
    }
    eligible["inventory_priority_score"] = sum(
        eligible[column].rank(pct=True) * weight
        for column, weight in score_inputs.items()
    ) * 100
    return eligible.sort_values(
        ["inventory_priority_score", "profit"], ascending=False
    ).head(limit).reset_index(drop=True)


def build_business_context(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create the compact, trusted evidence package supplied to the AI."""
    validate_analysis_data(df)
    products = build_product_summary(df)
    context = {
        "KPI SUMMARY": build_kpi_summary(df),
        "YEARLY PERFORMANCE": build_yearly_summary(df),
        "REGIONAL PERFORMANCE": build_dimension_summary(df, "region"),
        "CATEGORY PERFORMANCE": build_dimension_summary(df, "category"),
        "SUB-CATEGORY PERFORMANCE": build_dimension_summary(df, "sub_category"),
        "SEGMENT PERFORMANCE": build_dimension_summary(df, "segment"),
        "SHIP MODE PERFORMANCE": build_dimension_summary(df, "ship_mode"),
        "DISCOUNT PERFORMANCE": build_discount_summary(df),
        "INVENTORY PRIORITY PROXY": build_inventory_priority(df),
        "TOP PRODUCTS BY SALES": products.nlargest(10, "sales"),
        "TOP PRODUCTS BY PROFIT": products.nlargest(10, "profit"),
        "WORST PRODUCTS BY PROFIT": products.nsmallest(10, "profit"),
    }
    if "state" in df.columns:
        states = build_dimension_summary(df, "state")
        context["TOP STATES BY SALES"] = states.nlargest(10, "sales")
        context["WORST STATES BY PROFIT"] = states.nsmallest(10, "profit")
    return context


def context_to_text(context: dict[str, pd.DataFrame]) -> str:
    """Serialize evidence tables into a compact, model-readable format."""
    return "\n".join(
        f"\n### {name}\n{table.to_csv(index=False, float_format='%.4f')}"
        for name, table in context.items()
        if isinstance(table, pd.DataFrame) and not table.empty
    )
