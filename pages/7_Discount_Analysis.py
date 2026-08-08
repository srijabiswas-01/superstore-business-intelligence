import streamlit as st

from utils.theme import apply_dashboard_theme
import pandas as pd
import numpy as np
import plotly.express as px

from utils.data_loader import load_processed_data
from utils.filters import sidebar_filters


st.set_page_config(
    page_title="Discount Analysis",
    layout="wide"
)

apply_dashboard_theme()

st.title(" Discount and Pricing Analysis")

st.caption(
    "Discount exposure, profitability impact, pricing risk and promotional efficiency"
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
# BASIC DISCOUNT METRICS
# --------------------------------------------------

average_discount = filtered_df["discount"].mean() * 100

discounted_transactions = filtered_df[
    filtered_df["discount"] > 0
]

high_discount_transactions = filtered_df[
    filtered_df["discount"] > 0.30
]

discounted_sales = discounted_transactions["sales"].sum()

discounted_profit = discounted_transactions["profit"].sum()

high_discount_profit = high_discount_transactions["profit"].sum()

high_discount_sales = high_discount_transactions["sales"].sum()

discounted_transaction_rate = (
    len(discounted_transactions)
    / len(filtered_df)
    * 100
)

high_discount_rate = (
    len(high_discount_transactions)
    / len(filtered_df)
    * 100
)


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Average Discount",
    f"{average_discount:.1f}%"
)

col2.metric(
    "Discounted Transactions",
    f"{discounted_transaction_rate:.1f}%"
)

col3.metric(
    "Sales under Discount",
    f"${discounted_sales:,.0f}"
)

col4.metric(
    "Profit under Discount",
    f"${discounted_profit:,.0f}"
)


col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "High-Discount Transactions",
    f"{high_discount_rate:.1f}%"
)

col6.metric(
    "High-Discount Sales",
    f"${high_discount_sales:,.0f}"
)

col7.metric(
    "High-Discount Profit",
    f"${high_discount_profit:,.0f}"
)

loss_discounted_orders = discounted_transactions[
    discounted_transactions["profit"] < 0
]["order_id"].nunique()

col8.metric(
    "Loss-Making Discounted Orders",
    f"{loss_discounted_orders:,}"
)


st.divider()


# --------------------------------------------------
# DISCOUNT BAND SUMMARY
# --------------------------------------------------

discount_summary = (
    filtered_df
    .groupby(
        "discount_band",
        observed=False,
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        quantity=("quantity", "sum"),
        average_discount=("discount", "mean")
    )
)

discount_summary["profit_margin_pct"] = np.where(
    discount_summary["sales"] != 0,
    discount_summary["profit"]
    / discount_summary["sales"]
    * 100,
    0
)

discount_summary["average_discount_pct"] = (
    discount_summary["average_discount"]
    * 100
)


# --------------------------------------------------
# DISCOUNT BAND PERFORMANCE
# --------------------------------------------------

left, right = st.columns(2)

with left:

    fig_discount_sales = px.bar(
        discount_summary,
        x="discount_band",
        y="sales",
        text_auto=".2s",
        title="Sales by Discount Band"
    )

    st.plotly_chart(
        fig_discount_sales,
        width="stretch"
    )

with right:

    fig_discount_profit = px.bar(
        discount_summary,
        x="discount_band",
        y="profit",
        text_auto=".2s",
        title="Profit by Discount Band"
    )

    st.plotly_chart(
        fig_discount_profit,
        width="stretch"
    )


# --------------------------------------------------
# PROFIT MARGIN BY DISCOUNT BAND
# --------------------------------------------------

fig_discount_margin = px.bar(
    discount_summary,
    x="discount_band",
    y="profit_margin_pct",
    text_auto=".1f",
    title="Profit Margin by Discount Band"
)

fig_discount_margin.update_layout(
    xaxis_title="Discount Band",
    yaxis_title="Profit Margin (%)"
)

st.plotly_chart(
    fig_discount_margin,
    width="stretch"
)


# --------------------------------------------------
# DISCOUNT VS PROFIT SCATTER
# --------------------------------------------------

fig_discount_profit_scatter = px.scatter(
    filtered_df,
    x="discount",
    y="profit",
    size="sales",
    color="category",
    hover_data=[
        "product_name",
        "sub_category",
        "region",
        "segment"
    ],
    title="Transaction Discount vs Profit"
)

fig_discount_profit_scatter.update_layout(
    xaxis_title="Discount",
    yaxis_title="Profit ($)"
)

st.plotly_chart(
    fig_discount_profit_scatter,
    width="stretch"
)


# --------------------------------------------------
# DISCOUNT VS PROFIT MARGIN
# --------------------------------------------------

scatter_df = filtered_df.copy()

scatter_df = scatter_df[
    scatter_df["sales"] > 0
]

fig_discount_margin_scatter = px.scatter(
    scatter_df,
    x="discount",
    y="profit_margin_pct",
    color="category",
    size="sales",
    hover_name="product_name",
    hover_data=[
        "sub_category",
        "region",
        "segment"
    ],
    title="Discount vs Profit Margin"
)

st.plotly_chart(
    fig_discount_margin_scatter,
    width="stretch"
)


# --------------------------------------------------
# CATEGORY DISCOUNT EXPOSURE
# --------------------------------------------------

category_discount = (
    filtered_df
    .groupby(
        "category",
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        average_discount=("discount", "mean"),
        orders=("order_id", "nunique")
    )
)

category_discount["average_discount_pct"] = (
    category_discount["average_discount"]
    * 100
)

category_discount["profit_margin_pct"] = np.where(
    category_discount["sales"] != 0,
    category_discount["profit"]
    / category_discount["sales"]
    * 100,
    0
)


left, right = st.columns(2)

with left:

    fig_category_discount = px.bar(
        category_discount.sort_values(
            "average_discount_pct",
            ascending=False
        ),
        x="category",
        y="average_discount_pct",
        text_auto=".1f",
        title="Average Discount by Category"
    )

    st.plotly_chart(
        fig_category_discount,
        width="stretch"
    )

with right:

    fig_category_margin = px.bar(
        category_discount.sort_values(
            "profit_margin_pct",
            ascending=False
        ),
        x="category",
        y="profit_margin_pct",
        text_auto=".1f",
        title="Profit Margin by Category"
    )

    st.plotly_chart(
        fig_category_margin,
        width="stretch"
    )


# --------------------------------------------------
# REGION DISCOUNT EXPOSURE
# --------------------------------------------------

region_discount = (
    filtered_df
    .groupby(
        "region",
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        average_discount=("discount", "mean"),
        orders=("order_id", "nunique")
    )
)

region_discount["average_discount_pct"] = (
    region_discount["average_discount"]
    * 100
)

region_discount["profit_margin_pct"] = np.where(
    region_discount["sales"] != 0,
    region_discount["profit"]
    / region_discount["sales"]
    * 100,
    0
)


left, right = st.columns(2)

with left:

    fig_region_discount = px.bar(
        region_discount.sort_values(
            "average_discount_pct",
            ascending=False
        ),
        x="region",
        y="average_discount_pct",
        text_auto=".1f",
        title="Average Discount by Region"
    )

    st.plotly_chart(
        fig_region_discount,
        width="stretch"
    )

with right:

    fig_region_margin = px.bar(
        region_discount.sort_values(
            "profit_margin_pct",
            ascending=False
        ),
        x="region",
        y="profit_margin_pct",
        text_auto=".1f",
        title="Regional Profit Margin"
    )

    st.plotly_chart(
        fig_region_margin,
        width="stretch"
    )


# --------------------------------------------------
# SEGMENT DISCOUNT EXPOSURE
# --------------------------------------------------

segment_discount = (
    filtered_df
    .groupby(
        "segment",
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        average_discount=("discount", "mean"),
        orders=("order_id", "nunique")
    )
)

segment_discount["average_discount_pct"] = (
    segment_discount["average_discount"]
    * 100
)

segment_discount["profit_margin_pct"] = np.where(
    segment_discount["sales"] != 0,
    segment_discount["profit"]
    / segment_discount["sales"]
    * 100,
    0
)


fig_segment_discount = px.bar(
    segment_discount,
    x="segment",
    y="average_discount_pct",
    text_auto=".1f",
    title="Average Discount by Customer Segment"
)

st.plotly_chart(
    fig_segment_discount,
    width="stretch"
)


# --------------------------------------------------
# SUB-CATEGORY PRICING RISK
# --------------------------------------------------

st.subheader("Sub-Category Pricing Risk")


subcategory_discount = (
    filtered_df
    .groupby(
        "sub_category",
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        average_discount=("discount", "mean"),
        orders=("order_id", "nunique")
    )
)

subcategory_discount["average_discount_pct"] = (
    subcategory_discount["average_discount"]
    * 100
)

subcategory_discount["profit_margin_pct"] = np.where(
    subcategory_discount["sales"] != 0,
    subcategory_discount["profit"]
    / subcategory_discount["sales"]
    * 100,
    0
)


fig_subcategory_risk = px.scatter(
    subcategory_discount,
    x="average_discount_pct",
    y="profit_margin_pct",
    size="sales",
    color="profit",
    hover_name="sub_category",
    title="Sub-Category Discount vs Profit Margin"
)

st.plotly_chart(
    fig_subcategory_risk,
    width="stretch"
)


# --------------------------------------------------
# DISCOUNT RISK CLASSIFICATION
# --------------------------------------------------

discount_median = (
    subcategory_discount[
        "average_discount_pct"
    ].median()
)

margin_median = (
    subcategory_discount[
        "profit_margin_pct"
    ].median()
)


def classify_pricing_risk(row):
    """Classify pricing risk from discount and margin relative to their medians."""

    if (
        row["average_discount_pct"]
        >= discount_median
        and
        row["profit_margin_pct"]
        < margin_median
    ):
        return "High Discount / Margin Risk"

    elif (
        row["average_discount_pct"]
        < discount_median
        and
        row["profit_margin_pct"]
        >= margin_median
    ):
        return "Pricing Strength"

    elif (
        row["average_discount_pct"]
        >= discount_median
        and
        row["profit_margin_pct"]
        >= margin_median
    ):
        return "Discount Supported"

    else:
        return "Review"


subcategory_discount["pricing_group"] = (
    subcategory_discount.apply(
        classify_pricing_risk,
        axis=1
    )
)


fig_pricing_matrix = px.scatter(
    subcategory_discount,
    x="average_discount_pct",
    y="profit_margin_pct",
    size="sales",
    color="pricing_group",
    hover_name="sub_category",
    title="Pricing Risk Matrix"
)

fig_pricing_matrix.add_vline(
    x=discount_median,
    line_dash="dash"
)

fig_pricing_matrix.add_hline(
    y=margin_median,
    line_dash="dash"
)

st.plotly_chart(
    fig_pricing_matrix,
    width="stretch"
)


# --------------------------------------------------
# HIGH-DISCOUNT PRODUCTS
# --------------------------------------------------

st.subheader("High-Discount Product Exposure")


product_discount = (
    filtered_df
    .groupby(
        [
            "product_name",
            "category",
            "sub_category"
        ],
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        average_discount=("discount", "mean"),
        orders=("order_id", "nunique")
    )
)

product_discount["average_discount_pct"] = (
    product_discount["average_discount"]
    * 100
)

product_discount["profit_margin_pct"] = np.where(
    product_discount["sales"] != 0,
    product_discount["profit"]
    / product_discount["sales"]
    * 100,
    0
)


high_discount_products = (
    product_discount[
        product_discount[
            "average_discount_pct"
        ] >= 30
    ]
    .sort_values(
        "profit"
    )
)


if not high_discount_products.empty:

    st.warning(
        f"{len(high_discount_products)} products receive "
        "an average discount of at least 30%."
    )

    st.dataframe(
        high_discount_products[
            [
                "product_name",
                "category",
                "sub_category",
                "sales",
                "profit",
                "average_discount_pct",
                "profit_margin_pct",
                "orders"
            ]
        ],
        width="stretch"
    )

else:

    st.success(
        "No products currently have an average discount of 30% or more."
    )


# --------------------------------------------------
# IDENTIFY LOSS-MAKING DISCOUNT BANDS
# --------------------------------------------------

st.subheader("Pricing Risk Thresholds")


negative_discount_bands = (
    discount_summary[
        discount_summary["profit"] < 0
    ]
)


if not negative_discount_bands.empty:

    first_negative_band = (
        negative_discount_bands
        .iloc[0]
    )

    st.error(
        f"""
        At least one discount band is generating negative aggregate profit.

        The first identified loss-making band is:

        **{first_negative_band['discount_band']}**

        Sales:
        **${first_negative_band['sales']:,.0f}**

        Profit:
        **${first_negative_band['profit']:,.0f}**

        Profit Margin:
        **{first_negative_band['profit_margin_pct']:.1f}%**
        """
    )

else:

    st.success(
        "No discount band generates negative aggregate profit "
        "under the current filters."
    )


# --------------------------------------------------
# DISCOUNT CORRELATION
# --------------------------------------------------

discount_profit_corr = (
    filtered_df[
        ["discount", "profit"]
    ]
    .corr()
    .iloc[0, 1]
)

discount_margin_corr = (
    filtered_df[
        ["discount", "profit_margin_pct"]
    ]
    .corr()
    .iloc[0, 1]
)


corr1, corr2 = st.columns(2)

corr1.metric(
    "Discount vs Profit Correlation",
    f"{discount_profit_corr:.2f}"
)

corr2.metric(
    "Discount vs Margin Correlation",
    f"{discount_margin_corr:.2f}"
)

st.caption(
    "Correlation measures association only. It does not prove that discounting causes changes in profit."
)


# --------------------------------------------------
# DYNAMIC BUSINESS INSIGHTS
# --------------------------------------------------

st.divider()

st.subheader("Discount and Pricing Insights")


highest_discount_category = (
    category_discount
    .sort_values(
        "average_discount_pct",
        ascending=False
    )
    .iloc[0]
)

highest_discount_region = (
    region_discount
    .sort_values(
        "average_discount_pct",
        ascending=False
    )
    .iloc[0]
)

highest_discount_segment = (
    segment_discount
    .sort_values(
        "average_discount_pct",
        ascending=False
    )
    .iloc[0]
)

weakest_margin_category = (
    category_discount
    .sort_values(
        "profit_margin_pct"
    )
    .iloc[0]
)

strongest_discount_band = (
    discount_summary
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)

weakest_discount_band = (
    discount_summary
    .sort_values(
        "profit"
    )
    .iloc[0]
)


left, right = st.columns(2)

with left:

    st.success(
        f"""
        **Most Profitable Discount Band**

        {strongest_discount_band['discount_band']}

        Profit: ${strongest_discount_band['profit']:,.0f}

        Margin: {strongest_discount_band['profit_margin_pct']:.1f}%
        """
    )

    st.info(
        f"""
        **Highest Average Discount Category**

        {highest_discount_category['category']}

        Average Discount:
        {highest_discount_category['average_discount_pct']:.1f}%
        """
    )

    st.info(
        f"""
        **Highest Discount Customer Segment**

        {highest_discount_segment['segment']}

        Average Discount:
        {highest_discount_segment['average_discount_pct']:.1f}%
        """
    )


with right:

    if weakest_discount_band["profit"] < 0:

        st.error(
            f"""
            **Weakest Discount Band**

            {weakest_discount_band['discount_band']}

            Profit: ${weakest_discount_band['profit']:,.0f}

            Margin: {weakest_discount_band['profit_margin_pct']:.1f}%
            """
        )

    else:

        st.warning(
            f"""
            **Lowest-Profit Discount Band**

            {weakest_discount_band['discount_band']}

            Profit: ${weakest_discount_band['profit']:,.0f}
            """
        )

    st.warning(
        f"""
        **Highest Discount Region**

        {highest_discount_region['region']}

        Average Discount:
        {highest_discount_region['average_discount_pct']:.1f}%
        """
    )

    st.warning(
        f"""
        **Weakest Category Margin**

        {weakest_margin_category['category']}

        Margin:
        {weakest_margin_category['profit_margin_pct']:.1f}%
        """
    )


# --------------------------------------------------
# MANAGEMENT RECOMMENDATIONS
# --------------------------------------------------

st.subheader("Pricing Management Recommendations")


if not negative_discount_bands.empty:

    st.error(
        """
        **Review loss-making discount bands:**  
        Discount levels associated with negative aggregate profit should
        be investigated before being used as routine promotional policy.
        """
    )


if high_discount_profit < 0:

    st.error(
        f"""
        **High-discount profitability risk:**  
        Transactions above 30% discount currently generate
        **${high_discount_profit:,.0f}** in aggregate profit/loss.
        Management should consider stricter approval thresholds for deep discounts.
        """
    )


pricing_risks = (
    subcategory_discount[
        subcategory_discount[
            "pricing_group"
        ]
        == "High Discount / Margin Risk"
    ]
)


if not pricing_risks.empty:

    st.warning(
        f"""
        **Review pricing-risk sub-categories:**  
        {len(pricing_risks)} sub-categories combine relatively high discount
        levels with weaker profit margins.
        """
    )

    st.dataframe(
        pricing_risks[
            [
                "sub_category",
                "sales",
                "profit",
                "average_discount_pct",
                "profit_margin_pct"
            ]
        ],
        width="stretch"
    )


st.info(
    """
    Discounts should not be evaluated using sales alone.
    A promotional decision is stronger when additional sales compensate
    for the margin sacrificed through the discount.
    """
)


# --------------------------------------------------
# DETAIL TABLES
# --------------------------------------------------

with st.expander(
    "View Discount Band Performance"
):

    st.dataframe(
        discount_summary,
        width="stretch"
    )


with st.expander(
    "View Category Discount Performance"
):

    st.dataframe(
        category_discount,
        width="stretch"
    )


with st.expander(
    "View Pricing Risk by Sub-Category"
):

    st.dataframe(
        subcategory_discount.sort_values(
            "profit_margin_pct"
        ),
        width="stretch"
    )


# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------

st.divider()

discount_csv = (
    discount_summary
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    label="Download Discount Analysis",
    data=discount_csv,
    file_name="discount_analysis.csv",
    mime="text/csv"
)


pricing_risk_csv = (
    subcategory_discount
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    label="Download Pricing Risk Data",
    data=pricing_risk_csv,
    file_name="pricing_risk_analysis.csv",
    mime="text/csv"
)
