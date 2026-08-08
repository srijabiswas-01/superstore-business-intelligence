def calculate_kpis(df):
    """Calculate the common executive KPIs for the active data selection.

    Args:
        df: Processed and optionally filtered transaction DataFrame.

    Returns:
        A dictionary containing sales, profit, orders, customers, units,
        margin, order value, discount, shipping delay, and loss-order metrics.
        Ratios safely return zero when their denominator is zero.
    """
    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    orders = df["order_id"].nunique()
    customers = df["customer_id"].nunique()
    units = df["quantity"].sum()

    profit_margin = (
        total_profit / total_sales * 100
        if total_sales != 0
        else 0
    )

    average_order_value = (
        total_sales / orders
        if orders != 0
        else 0
    )

    average_discount = (
        df["discount"].mean() * 100
    )

    shipping_delay = (
        df["shipping_delay"].mean()
    )

    loss_orders = (
        df.loc[
            df["profit"] < 0,
            "order_id"
        ].nunique()
    )

    return {
        "total_sales": total_sales,
        "total_profit": total_profit,
        "orders": orders,
        "customers": customers,
        "units": units,
        "profit_margin": profit_margin,
        "average_order_value": average_order_value,
        "average_discount": average_discount,
        "shipping_delay": shipping_delay,
        "loss_orders": loss_orders
    }
