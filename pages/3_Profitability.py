import streamlit as st

from utils.theme import apply_dashboard_theme
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_processed_data
from utils.filters import sidebar_filters
from utils.kpi_engine import calculate_kpis


st.set_page_config(
    page_title="Profitability Analysis",
    layout="wide"
)

apply_dashboard_theme()

st.title("Profitability Analysis")

st.caption(
    "Profit trends, margin performance, loss concentration and profitability risk analysis"
)


# --------------------------------------------------
# LOAD AND FILTER DATA
# --------------------------------------------------

df = load_processed_data()
filtered_df = sidebar_filters(df)

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()


kpis = calculate_kpis(filtered_df)


# --------------------------------------------------
# YEARLY PROFITABILITY
# --------------------------------------------------

yearly_profit = (
    filtered_df
    .groupby("order_year", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique")
    )
    .sort_values("order_year")
)

yearly_profit["profit_margin_pct"] = np.where(
    yearly_profit["sales"] != 0,
    yearly_profit["profit"]
    / yearly_profit["sales"]
    * 100,
    0
)

yearly_profit["profit_growth_pct"] = (
    yearly_profit["profit"]
    .pct_change()
    * 100
)


# --------------------------------------------------
# LOSS METRICS
# --------------------------------------------------

loss_transactions = filtered_df[
    filtered_df["profit"] < 0
]

loss_value = abs(
    loss_transactions["profit"].sum()
)

loss_orders = (
    loss_transactions["order_id"]
    .nunique()
)

product_profit = (
    filtered_df
    .groupby("product_name", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        quantity=("quantity", "sum"),
        orders=("order_id", "nunique")
    )
)

loss_products = product_profit[
    product_profit["profit"] < 0
]

loss_product_count = len(loss_products)


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Profit",
    f"${kpis['total_profit']:,.0f}"
)

col2.metric(
    "Profit Margin",
    f"{kpis['profit_margin']:.1f}%"
)

col3.metric(
    "Loss-Making Orders",
    f"{loss_orders:,}"
)

col4.metric(
    "Loss Value",
    f"${loss_value:,.0f}"
)


col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "Loss-Making Products",
    f"{loss_product_count:,}"
)

best_year = (
    yearly_profit
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)

col6.metric(
    "Best Profit Year",
    int(best_year["order_year"]),
    f"${best_year['profit']:,.0f}"
)


best_margin_year = (
    yearly_profit
    .sort_values(
        "profit_margin_pct",
        ascending=False
    )
    .iloc[0]
)

col7.metric(
    "Best Margin Year",
    int(best_margin_year["order_year"]),
    f"{best_margin_year['profit_margin_pct']:.1f}%"
)


loss_rate = (
    len(loss_transactions)
    / len(filtered_df)
    * 100
    if len(filtered_df) != 0
    else 0
)

col8.metric(
    "Loss Transaction Rate",
    f"{loss_rate:.1f}%"
)


st.divider()


# --------------------------------------------------
# PROFIT TREND
# --------------------------------------------------

monthly_profit = (
    filtered_df
    .groupby("year_month", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum")
    )
)

monthly_profit["date"] = pd.to_datetime(
    monthly_profit["year_month"]
)


fig_profit_trend = px.line(
    monthly_profit,
    x="date",
    y="profit",
    markers=True,
    title="Monthly Profit Trend"
)

fig_profit_trend.update_layout(
    xaxis_title="Month",
    yaxis_title="Profit ($)"
)

st.plotly_chart(
    fig_profit_trend,
    width="stretch"
)


# --------------------------------------------------
# YEARLY PROFIT AND MARGIN
# --------------------------------------------------

left, right = st.columns(2)


with left:

    fig_yearly_profit = px.bar(
        yearly_profit,
        x="order_year",
        y="profit",
        text_auto=".2s",
        title="Annual Profit Performance"
    )

    fig_yearly_profit.update_layout(
        xaxis_title="Year",
        yaxis_title="Profit ($)"
    )

    st.plotly_chart(
        fig_yearly_profit,
        width="stretch"
    )


with right:

    fig_margin = px.line(
        yearly_profit,
        x="order_year",
        y="profit_margin_pct",
        markers=True,
        title="Annual Profit Margin"
    )

    fig_margin.update_layout(
        xaxis_title="Year",
        yaxis_title="Profit Margin (%)"
    )

    st.plotly_chart(
        fig_margin,
        width="stretch"
    )


# --------------------------------------------------
# PROFIT GROWTH
# --------------------------------------------------

profit_growth_data = yearly_profit.dropna(
    subset=["profit_growth_pct"]
)

fig_profit_growth = px.bar(
    profit_growth_data,
    x="order_year",
    y="profit_growth_pct",
    text_auto=".1f",
    title="Year-on-Year Profit Growth"
)

fig_profit_growth.update_layout(
    xaxis_title="Year",
    yaxis_title="Profit Growth (%)"
)

st.plotly_chart(
    fig_profit_growth,
    width="stretch"
)


# --------------------------------------------------
# CATEGORY PROFITABILITY
# --------------------------------------------------

category_profit = (
    filtered_df
    .groupby("category", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique")
    )
)

category_profit["profit_margin_pct"] = np.where(
    category_profit["sales"] != 0,
    category_profit["profit"]
    / category_profit["sales"]
    * 100,
    0
)


region_profit = (
    filtered_df
    .groupby("region", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique")
    )
)

region_profit["profit_margin_pct"] = np.where(
    region_profit["sales"] != 0,
    region_profit["profit"]
    / region_profit["sales"]
    * 100,
    0
)


left, right = st.columns(2)


with left:

    fig_category_profit = px.bar(
        category_profit.sort_values(
            "profit",
            ascending=False
        ),
        x="category",
        y="profit",
        text_auto=".2s",
        title="Profit by Category"
    )

    st.plotly_chart(
        fig_category_profit,
        width="stretch"
    )


with right:

    fig_region_profit = px.bar(
        region_profit.sort_values(
            "profit",
            ascending=False
        ),
        x="region",
        y="profit",
        text_auto=".2s",
        title="Profit by Region"
    )

    st.plotly_chart(
        fig_region_profit,
        width="stretch"
    )


# --------------------------------------------------
# SALES VS PROFIT MATRIX
# --------------------------------------------------

st.subheader("Sales vs Profit Performance Matrix")

matrix_data = (
    filtered_df
    .groupby("sub_category", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique")
    )
)

sales_median = matrix_data["sales"].median()
profit_median = matrix_data["profit"].median()


def classify_performance(row):
    """Classify a record into the sales/profit matrix using current medians.

    The surrounding page calculates ``sales_median`` and ``profit_median`` from
    the active filter selection; this helper returns the matching strategic label.
    """

    if (
        row["sales"] >= sales_median
        and row["profit"] >= profit_median
    ):
        return "Stars"

    elif (
        row["sales"] >= sales_median
        and row["profit"] < profit_median
    ):
        return "Margin Risk"

    elif (
        row["sales"] < sales_median
        and row["profit"] >= profit_median
    ):
        return "Growth Opportunity"

    else:
        return "Review / Low Performance"


matrix_data["performance_group"] = (
    matrix_data.apply(
        classify_performance,
        axis=1
    )
)


fig_matrix = px.scatter(
    matrix_data,
    x="sales",
    y="profit",
    size="orders",
    color="performance_group",
    hover_name="sub_category",
    title="Sub-Category Sales vs Profit Matrix"
)

fig_matrix.add_vline(
    x=sales_median,
    line_dash="dash"
)

fig_matrix.add_hline(
    y=profit_median,
    line_dash="dash"
)

fig_matrix.update_layout(
    xaxis_title="Sales ($)",
    yaxis_title="Profit ($)"
)

st.plotly_chart(
    fig_matrix,
    width="stretch"
)


# --------------------------------------------------
# PRODUCT LOSS ANALYSIS
# --------------------------------------------------

st.subheader("Product Profitability Risk")


left, right = st.columns(2)


with left:

    top_profit_products = (
        product_profit
        .nlargest(
            10,
            "profit"
        )
        .sort_values("profit")
    )

    fig_top_profit = px.bar(
        top_profit_products,
        x="profit",
        y="product_name",
        orientation="h",
        title="Top 10 Products by Profit"
    )

    st.plotly_chart(
        fig_top_profit,
        width="stretch"
    )


with right:

    worst_profit_products = (
        product_profit
        .nsmallest(
            10,
            "profit"
        )
        .sort_values("profit")
    )

    fig_worst_profit = px.bar(
        worst_profit_products,
        x="profit",
        y="product_name",
        orientation="h",
        title="Bottom 10 Products by Profit"
    )

    st.plotly_chart(
        fig_worst_profit,
        width="stretch"
    )


# --------------------------------------------------
# SUB-CATEGORY LOSS ANALYSIS
# --------------------------------------------------

subcat_profit = (
    filtered_df
    .groupby("sub_category", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique")
    )
)

subcat_profit["profit_margin_pct"] = np.where(
    subcat_profit["sales"] != 0,
    subcat_profit["profit"]
    / subcat_profit["sales"]
    * 100,
    0
)


fig_subcat = px.bar(
    subcat_profit.sort_values("profit"),
    x="profit",
    y="sub_category",
    orientation="h",
    title="Sub-Category Profitability"
)

st.plotly_chart(
    fig_subcat,
    width="stretch"
)


# --------------------------------------------------
# HIGH SALES / LOW PROFIT IDENTIFICATION
# --------------------------------------------------

st.subheader("High Sales but Weak Profitability")


high_sales_threshold = (
    product_profit["sales"].quantile(0.75)
)

low_profit_threshold = (
    product_profit["profit"].median()
)


margin_risk_products = (
    product_profit[
        (
            product_profit["sales"]
            >= high_sales_threshold
        )
        &
        (
            product_profit["profit"]
            <= low_profit_threshold
        )
    ]
    .sort_values("sales", ascending=False)
)


if not margin_risk_products.empty:

    st.warning(
        f"{len(margin_risk_products)} products have relatively high sales "
        "but weak profitability within the selected data."
    )

    st.dataframe(
        margin_risk_products,
        width="stretch"
    )

else:

    st.success(
        "No clear high-sales/weak-profit products were identified "
        "under the current filters."
    )


# --------------------------------------------------
# DYNAMIC PROFITABILITY INSIGHTS
# --------------------------------------------------

st.divider()

st.subheader("Profitability Insights")


best_region = (
    region_profit
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)

worst_region = (
    region_profit
    .sort_values("profit")
    .iloc[0]
)

best_category = (
    category_profit
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)

weakest_category = (
    category_profit
    .sort_values(
        "profit_margin_pct"
    )
    .iloc[0]
)

worst_product = (
    product_profit
    .sort_values("profit")
    .iloc[0]
)

worst_subcat = (
    subcat_profit
    .sort_values("profit")
    .iloc[0]
)


insight1, insight2 = st.columns(2)


with insight1:

    st.success(
        f"""
        **Most Profitable Region**

        {best_region['region']}

        Profit: ${best_region['profit']:,.0f}

        Margin: {best_region['profit_margin_pct']:.1f}%
        """
    )

    st.success(
        f"""
        **Most Profitable Category**

        {best_category['category']}

        Profit: ${best_category['profit']:,.0f}

        Margin: {best_category['profit_margin_pct']:.1f}%
        """
    )


with insight2:

    if worst_region["profit"] < 0:

        st.error(
            f"""
            **Regional Profit Risk**

            {worst_region['region']}

            Profit: ${worst_region['profit']:,.0f}
            """
        )

    else:

        st.warning(
            f"""
            **Lowest Profit Region**

            {worst_region['region']}

            Profit: ${worst_region['profit']:,.0f}
            """
        )

    st.warning(
        f"""
        **Weakest Category Margin**

        {weakest_category['category']}

        Margin: {weakest_category['profit_margin_pct']:.1f}%
        """
    )


st.error(
    f"""
    **Largest Product Loss**

    {worst_product['product_name']}

    Sales: ${worst_product['sales']:,.0f}

    Profit: ${worst_product['profit']:,.0f}
    """
)


# --------------------------------------------------
# MANAGEMENT SUMMARY
# --------------------------------------------------

st.subheader("Profitability Management Summary")


summary = f"""
The selected business view generated
**${kpis['total_profit']:,.0f} in profit**
from **${kpis['total_sales']:,.0f} in sales**,
representing an overall profit margin of
**{kpis['profit_margin']:.1f}%**.

The strongest region by profit is
**{best_region['region']}**, while
**{best_category['category']}** is the
highest-profit category.

The weakest category by margin is
**{weakest_category['category']}**,
with a margin of
**{weakest_category['profit_margin_pct']:.1f}%**.

The largest product-level loss contributor is
**{worst_product['product_name']}**,
which generated
**${worst_product['profit']:,.0f} in profit/loss**.

The sub-category requiring the greatest attention is
**{worst_subcat['sub_category']}**,
with total profit of
**${worst_subcat['profit']:,.0f}**.
"""

st.markdown(summary)


# --------------------------------------------------
# MANAGEMENT ACTIONS
# --------------------------------------------------

st.subheader("Recommended Management Actions")


if loss_product_count > 0:

    st.error(
        f"Review the {loss_product_count} products that currently generate "
        "negative aggregate profit."
    )


if weakest_category["profit_margin_pct"] < 5:

    st.warning(
        f"Review pricing, discounting and product mix within "
        f"{weakest_category['category']} because its profit margin is relatively weak."
    )


if not margin_risk_products.empty:

    st.warning(
        "Investigate high-sales products with weak profitability. "
        "Strong revenue alone should not justify continued pricing or promotional policies."
    )


st.info(
    "Use the Discount Analysis page later to determine whether heavy discounting "
    "is associated with the identified profitability risks."
)


# --------------------------------------------------
# DETAILED TABLES
# --------------------------------------------------

with st.expander(
    "View Annual Profitability Data"
):

    annual_display = yearly_profit.copy()

    annual_display[
        "profit_margin_pct"
    ] = annual_display[
        "profit_margin_pct"
    ].round(2)

    annual_display[
        "profit_growth_pct"
    ] = annual_display[
        "profit_growth_pct"
    ].round(2)

    st.dataframe(
        annual_display,
        width="stretch"
    )


with st.expander(
    "View Loss-Making Products"
):

    st.dataframe(
        loss_products.sort_values("profit"),
        width="stretch"
    )


# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------

st.divider()

profitability_csv = product_profit.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="Download Product Profitability Data",
    data=profitability_csv,
    file_name="product_profitability_analysis.csv",
    mime="text/csv"
)
