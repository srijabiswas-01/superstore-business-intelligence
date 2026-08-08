import streamlit as st

from utils.theme import apply_dashboard_theme
import pandas as pd
import numpy as np
import plotly.express as px

from utils.data_loader import load_processed_data
from utils.filters import sidebar_filters


st.set_page_config(
    page_title="Operations Analysis",
    layout="wide"
)

apply_dashboard_theme()

st.title("Operations and Shipping Analysis")

st.caption(
    "Shipping efficiency, delivery delays, operational bottlenecks and fulfilment performance"
)


# --------------------------------------------------
# LOAD AND FILTER DATA
# --------------------------------------------------

df = load_processed_data()
filtered_df = sidebar_filters(df)

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()


# --------------------------------------------------
# BASIC SHIPPING METRICS
# --------------------------------------------------

avg_shipping_delay = filtered_df["shipping_delay"].mean()

median_shipping_delay = filtered_df["shipping_delay"].median()

max_shipping_delay = filtered_df["shipping_delay"].max()

min_shipping_delay = filtered_df["shipping_delay"].min()

delayed_orders = filtered_df[
    filtered_df["shipping_delay"] >
    filtered_df["shipping_delay"].median()
]

delayed_order_count = delayed_orders[
    "order_id"
].nunique()

total_orders = filtered_df[
    "order_id"
].nunique()

delay_rate = (
    delayed_order_count / total_orders * 100
    if total_orders != 0
    else 0
)


# --------------------------------------------------
# SHIP MODE SUMMARY
# --------------------------------------------------

ship_mode_summary = (
    filtered_df
    .groupby("ship_mode", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        quantity=("quantity", "sum"),
        avg_shipping_delay=("shipping_delay", "mean"),
        median_shipping_delay=("shipping_delay", "median"),
        average_discount=("discount", "mean")
    )
)

ship_mode_summary["profit_margin_pct"] = np.where(
    ship_mode_summary["sales"] != 0,
    ship_mode_summary["profit"]
    / ship_mode_summary["sales"]
    * 100,
    0
)


fastest_mode = (
    ship_mode_summary
    .sort_values(
        "avg_shipping_delay"
    )
    .iloc[0]
)

slowest_mode = (
    ship_mode_summary
    .sort_values(
        "avg_shipping_delay",
        ascending=False
    )
    .iloc[0]
)

most_used_mode = (
    ship_mode_summary
    .sort_values(
        "orders",
        ascending=False
    )
    .iloc[0]
)


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Average Shipping Delay",
    f"{avg_shipping_delay:.1f} days"
)

col2.metric(
    "Median Shipping Delay",
    f"{median_shipping_delay:.1f} days"
)

col3.metric(
    "Fastest Ship Mode",
    fastest_mode["ship_mode"],
    f"{fastest_mode['avg_shipping_delay']:.1f} days"
)

col4.metric(
    "Slowest Ship Mode",
    slowest_mode["ship_mode"],
    f"{slowest_mode['avg_shipping_delay']:.1f} days"
)


col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "Maximum Shipping Delay",
    f"{max_shipping_delay:.0f} days"
)

col6.metric(
    "Minimum Shipping Delay",
    f"{min_shipping_delay:.0f} days"
)

col7.metric(
    "Most Used Ship Mode",
    most_used_mode["ship_mode"],
    f"{int(most_used_mode['orders']):,} orders"
)

col8.metric(
    "Above-Median Delay Orders",
    f"{delay_rate:.1f}%"
)


st.divider()


# --------------------------------------------------
# SHIP MODE PERFORMANCE
# --------------------------------------------------

st.subheader("Ship Mode Performance")


left, right = st.columns(2)


with left:

    fig_mode_delay = px.bar(
        ship_mode_summary.sort_values(
            "avg_shipping_delay"
        ),
        x="ship_mode",
        y="avg_shipping_delay",
        text_auto=".1f",
        title="Average Shipping Delay by Ship Mode"
    )

    fig_mode_delay.update_layout(
        xaxis_title="Ship Mode",
        yaxis_title="Average Delay (Days)"
    )

    st.plotly_chart(
        fig_mode_delay,
        width="stretch"
    )


with right:

    fig_mode_orders = px.bar(
        ship_mode_summary.sort_values(
            "orders",
            ascending=False
        ),
        x="ship_mode",
        y="orders",
        text_auto=True,
        title="Order Volume by Ship Mode"
    )

    st.plotly_chart(
        fig_mode_orders,
        width="stretch"
    )


# --------------------------------------------------
# SHIP MODE SALES AND PROFIT
# --------------------------------------------------

fig_mode_financial = px.bar(
    ship_mode_summary,
    x="ship_mode",
    y=["sales", "profit"],
    barmode="group",
    title="Sales and Profit by Ship Mode"
)

st.plotly_chart(
    fig_mode_financial,
    width="stretch"
)


# --------------------------------------------------
# SHIPPING DELAY DISTRIBUTION
# --------------------------------------------------

st.subheader("Shipping Delay Distribution")


fig_delay_hist = px.histogram(
    filtered_df,
    x="shipping_delay",
    nbins=20,
    title="Distribution of Shipping Delay"
)

fig_delay_hist.update_layout(
    xaxis_title="Shipping Delay (Days)",
    yaxis_title="Transactions"
)

st.plotly_chart(
    fig_delay_hist,
    width="stretch"
)


# --------------------------------------------------
# REGION SHIPPING PERFORMANCE
# --------------------------------------------------

st.subheader("Regional Operational Performance")


region_shipping = (
    filtered_df
    .groupby("region", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        avg_shipping_delay=("shipping_delay", "mean"),
        median_shipping_delay=("shipping_delay", "median")
    )
)

region_shipping["profit_margin_pct"] = np.where(
    region_shipping["sales"] != 0,
    region_shipping["profit"]
    / region_shipping["sales"]
    * 100,
    0
)


left, right = st.columns(2)


with left:

    fig_region_delay = px.bar(
        region_shipping.sort_values(
            "avg_shipping_delay",
            ascending=False
        ),
        x="region",
        y="avg_shipping_delay",
        text_auto=".1f",
        title="Average Shipping Delay by Region"
    )

    st.plotly_chart(
        fig_region_delay,
        width="stretch"
    )


with right:

    fig_region_operations = px.scatter(
        region_shipping,
        x="avg_shipping_delay",
        y="profit",
        size="orders",
        color="region",
        hover_name="region",
        hover_data=[
            "sales",
            "profit_margin_pct"
        ],
        title="Regional Shipping Delay vs Profit"
    )

    st.plotly_chart(
        fig_region_operations,
        width="stretch"
    )


# --------------------------------------------------
# CATEGORY SHIPPING PERFORMANCE
# --------------------------------------------------

st.subheader("Category Fulfilment Performance")


category_shipping = (
    filtered_df
    .groupby("category", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        avg_shipping_delay=("shipping_delay", "mean")
    )
)

left, right = st.columns(2)


with left:

    fig_category_delay = px.bar(
        category_shipping.sort_values(
            "avg_shipping_delay",
            ascending=False
        ),
        x="category",
        y="avg_shipping_delay",
        text_auto=".1f",
        title="Average Shipping Delay by Category"
    )

    st.plotly_chart(
        fig_category_delay,
        width="stretch"
    )


with right:

    fig_category_ops = px.scatter(
        category_shipping,
        x="avg_shipping_delay",
        y="profit",
        size="sales",
        color="category",
        hover_name="category",
        title="Category Shipping Delay vs Profit"
    )

    st.plotly_chart(
        fig_category_ops,
        width="stretch"
    )


# --------------------------------------------------
# SUB-CATEGORY SHIPPING PERFORMANCE
# --------------------------------------------------

st.subheader("Sub-Category Delay Analysis")


subcategory_shipping = (
    filtered_df
    .groupby("sub_category", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        avg_shipping_delay=("shipping_delay", "mean")
    )
)


fig_subcat_delay = px.bar(
    subcategory_shipping.sort_values(
        "avg_shipping_delay"
    ),
    x="avg_shipping_delay",
    y="sub_category",
    orientation="h",
    title="Average Shipping Delay by Sub-Category"
)

st.plotly_chart(
    fig_subcat_delay,
    width="stretch"
)


# --------------------------------------------------
# STATE OPERATIONS
# --------------------------------------------------

st.subheader("State-Level Operational Risk")


state_shipping = (
    filtered_df
    .groupby(
        ["state", "region"],
        as_index=False
    )
    .agg(
        orders=("order_id", "nunique"),
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        avg_shipping_delay=("shipping_delay", "mean")
    )
)


slow_states = (
    state_shipping
    .sort_values(
        "avg_shipping_delay",
        ascending=False
    )
    .head(15)
)


fig_slow_states = px.bar(
    slow_states.sort_values(
        "avg_shipping_delay"
    ),
    x="avg_shipping_delay",
    y="state",
    orientation="h",
    color="region",
    title="Top 15 States by Average Shipping Delay"
)

st.plotly_chart(
    fig_slow_states,
    width="stretch"
)


# --------------------------------------------------
# SHIPPING DELAY VS FINANCIAL PERFORMANCE
# --------------------------------------------------

st.subheader("Shipping Delay and Financial Performance")


delay_summary = (
    filtered_df
    .groupby(
        "shipping_delay",
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique")
    )
)


fig_delay_profit = px.scatter(
    delay_summary,
    x="shipping_delay",
    y="profit",
    size="orders",
    color="sales",
    title="Shipping Delay vs Aggregate Profit"
)

st.plotly_chart(
    fig_delay_profit,
    width="stretch"
)


# --------------------------------------------------
# CORRELATION
# --------------------------------------------------

delay_profit_corr = (
    filtered_df[
        ["shipping_delay", "profit"]
    ]
    .corr()
    .iloc[0, 1]
)

delay_sales_corr = (
    filtered_df[
        ["shipping_delay", "sales"]
    ]
    .corr()
    .iloc[0, 1]
)


corr1, corr2 = st.columns(2)

corr1.metric(
    "Shipping Delay vs Profit Correlation",
    f"{delay_profit_corr:.2f}"
)

corr2.metric(
    "Shipping Delay vs Sales Correlation",
    f"{delay_sales_corr:.2f}"
)

st.caption(
    "Correlation shows association only and does not prove that shipping delay causes changes in sales or profit."
)


# --------------------------------------------------
# OPERATIONS RISK CLASSIFICATION
# --------------------------------------------------

st.subheader("Operational Risk Classification")


region_delay_median = (
    region_shipping[
        "avg_shipping_delay"
    ].median()
)

region_profit_median = (
    region_shipping[
        "profit"
    ].median()
)


def classify_region_operations(row):
    """Classify regional operations using median delay and profit benchmarks."""

    if (
        row["avg_shipping_delay"]
        <= region_delay_median
        and
        row["profit"]
        >= region_profit_median
    ):
        return "Operational Strength"

    elif (
        row["avg_shipping_delay"]
        > region_delay_median
        and
        row["profit"]
        >= region_profit_median
    ):
        return "Delay Risk / Profitable"

    elif (
        row["avg_shipping_delay"]
        <= region_delay_median
        and
        row["profit"]
        < region_profit_median
    ):
        return "Efficient but Weak Profit"

    else:
        return "Operational Risk"


region_shipping["operations_group"] = (
    region_shipping.apply(
        classify_region_operations,
        axis=1
    )
)


fig_operations_matrix = px.scatter(
    region_shipping,
    x="avg_shipping_delay",
    y="profit",
    size="orders",
    color="operations_group",
    hover_name="region",
    hover_data=[
        "sales",
        "profit_margin_pct"
    ],
    title="Regional Operational Risk Matrix"
)

fig_operations_matrix.add_vline(
    x=region_delay_median,
    line_dash="dash"
)

fig_operations_matrix.add_hline(
    y=region_profit_median,
    line_dash="dash"
)

st.plotly_chart(
    fig_operations_matrix,
    width="stretch"
)


# --------------------------------------------------
# DYNAMIC OPERATIONAL INSIGHTS
# --------------------------------------------------

st.divider()

st.subheader("Operational Insights")


slowest_region = (
    region_shipping
    .sort_values(
        "avg_shipping_delay",
        ascending=False
    )
    .iloc[0]
)

fastest_region = (
    region_shipping
    .sort_values(
        "avg_shipping_delay"
    )
    .iloc[0]
)

slowest_category = (
    category_shipping
    .sort_values(
        "avg_shipping_delay",
        ascending=False
    )
    .iloc[0]
)

fastest_category = (
    category_shipping
    .sort_values(
        "avg_shipping_delay"
    )
    .iloc[0]
)

slowest_subcategory = (
    subcategory_shipping
    .sort_values(
        "avg_shipping_delay",
        ascending=False
    )
    .iloc[0]
)


left, right = st.columns(2)


with left:

    st.success(
        f"""
        **Fastest Shipping Mode**

        {fastest_mode['ship_mode']}

        Average Delay:
        {fastest_mode['avg_shipping_delay']:.1f} days

        Orders:
        {int(fastest_mode['orders']):,}
        """
    )

    st.success(
        f"""
        **Fastest Region**

        {fastest_region['region']}

        Average Delay:
        {fastest_region['avg_shipping_delay']:.1f} days
        """
    )

    st.info(
        f"""
        **Fastest Category**

        {fastest_category['category']}

        Average Delay:
        {fastest_category['avg_shipping_delay']:.1f} days
        """
    )


with right:

    st.warning(
        f"""
        **Slowest Shipping Mode**

        {slowest_mode['ship_mode']}

        Average Delay:
        {slowest_mode['avg_shipping_delay']:.1f} days
        """
    )

    st.warning(
        f"""
        **Slowest Region**

        {slowest_region['region']}

        Average Delay:
        {slowest_region['avg_shipping_delay']:.1f} days
        """
    )

    st.warning(
        f"""
        **Slowest Sub-Category**

        {slowest_subcategory['sub_category']}

        Average Delay:
        {slowest_subcategory['avg_shipping_delay']:.1f} days
        """
    )


# --------------------------------------------------
# OPERATIONAL RISK TABLE
# --------------------------------------------------

operational_risk_regions = (
    region_shipping[
        region_shipping[
            "operations_group"
        ]
        == "Operational Risk"
    ]
)


if not operational_risk_regions.empty:

    st.error(
        f"{len(operational_risk_regions)} region(s) combine relatively longer "
        "shipping delays with weaker profitability."
    )

    st.dataframe(
        operational_risk_regions,
        width="stretch"
    )


# --------------------------------------------------
# MANAGEMENT RECOMMENDATIONS
# --------------------------------------------------

st.subheader("Operations Management Recommendations")


st.success(
    f"""
    **Protect efficient fulfilment:**  
    {fastest_mode['ship_mode']} currently has the shortest average shipping delay
    at approximately {fastest_mode['avg_shipping_delay']:.1f} days.
    Management should identify whether its operational practices can be applied
    to slower fulfilment channels where commercially appropriate.
    """
)


if (
    slowest_mode["avg_shipping_delay"]
    >
    avg_shipping_delay
):

    st.warning(
        f"""
        **Review slower shipping modes:**  
        {slowest_mode['ship_mode']} is currently the slowest mode,
        averaging {slowest_mode['avg_shipping_delay']:.1f} days.
        Management should investigate whether this reflects the expected
        service design or an avoidable fulfilment issue.
        """
    )


if not operational_risk_regions.empty:

    st.error(
        """
        **Investigate operational-risk regions:**  
        Regions that combine longer delays with weaker profitability should be reviewed
        for logistics constraints, order mix and service configuration.
        """
    )


st.info(
    """
    The Sample Superstore dataset does not contain freight cost,
    warehouse capacity, carrier performance or customer satisfaction.
    Shipping analysis therefore identifies timing patterns and associations,
    not the underlying operational cause of delays.
    """
)


# --------------------------------------------------
# DETAILED TABLES
# --------------------------------------------------

with st.expander(
    "View Ship Mode Performance"
):

    st.dataframe(
        ship_mode_summary,
        width="stretch"
    )


with st.expander(
    "View Regional Shipping Performance"
):

    st.dataframe(
        region_shipping,
        width="stretch"
    )


with st.expander(
    "View State Shipping Performance"
):

    st.dataframe(
        state_shipping.sort_values(
            "avg_shipping_delay",
            ascending=False
        ),
        width="stretch"
    )


# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------

st.divider()

shipping_csv = (
    ship_mode_summary
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    label="Download Shipping Performance",
    data=shipping_csv,
    file_name="shipping_performance.csv",
    mime="text/csv"
)


state_shipping_csv = (
    state_shipping
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    label="Download State Operations Data",
    data=state_shipping_csv,
    file_name="state_operations_analysis.csv",
    mime="text/csv"
)
