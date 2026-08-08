import numpy as np
import pandas as pd


def create_features(df):
    """Derive reusable time, shipping, profitability, and discount features.

    Args:
        df: Cleaned transactions with parsed order and shipping dates.

    Returns:
        A copy containing calendar dimensions, shipping delay, profit/loss
        flags, unit economics, profit margin, and categorical discount bands.
    """
    df = df.copy()

    df["order_year"] = df["order_date"].dt.year
    df["order_quarter"] = "Q" + df["order_date"].dt.quarter.astype(str)
    df["order_month"] = df["order_date"].dt.month_name()
    df["order_month_num"] = df["order_date"].dt.month

    df["year_month"] = (
        df["order_date"]
        .dt.to_period("M")
        .astype(str)
    )

    df["shipping_delay"] = (
        df["ship_date"] - df["order_date"]
    ).dt.days

    df["profit_flag"] = (
        df["profit"] > 0
    ).astype(int)

    df["loss_flag"] = (
        df["profit"] < 0
    ).astype(int)

    df["profit_margin_pct"] = np.where(
        df["sales"] != 0,
        (df["profit"] / df["sales"]) * 100,
        0
    )

    df["sales_per_unit"] = np.where(
        df["quantity"] != 0,
        df["sales"] / df["quantity"],
        0
    )

    df["discount_band"] = pd.cut(
        df["discount"],
        bins=[-0.001, 0, 0.10, 0.20, 0.30, 1],
        labels=[
            "No Discount",
            "1–10%",
            "11–20%",
            "21–30%",
            "Above 30%"
        ]
    )

    return df
