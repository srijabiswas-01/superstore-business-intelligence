import streamlit as st

from utils.theme import apply_dashboard_theme
import pandas as pd
import plotly.express as px

from utils.data_loader import load_processed_data
from utils.filters import sidebar_filters


st.set_page_config(
    page_title="Sales Performance",
    layout="wide"
)

apply_dashboard_theme()

st.title("Sales Performance")

st.caption(
    "Revenue trends, growth patterns, seasonality and sales contribution analysis"
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
# YEARLY SALES SUMMARY
# --------------------------------------------------

yearly_sales = (
    filtered_df
    .groupby("order_year", as_index=False)
    .agg(
        sales=("sales", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        quantity=("quantity", "sum")
    )
    .sort_values("order_year")
)

yearly_sales["sales_growth_pct"] = (
    yearly_sales["sales"]
    .pct_change()
    * 100
)


# --------------------------------------------------
# MONTHLY SALES SUMMARY
# --------------------------------------------------

monthly_sales = (
    filtered_df
    .groupby(
        ["order_year", "order_month_num", "order_month"],
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique")
    )
)

monthly_sales["date"] = pd.to_datetime(
    monthly_sales["order_year"].astype(str)
    + "-"
    + monthly_sales["order_month_num"].astype(str)
    + "-01"
)


# --------------------------------------------------
# KPIs
# --------------------------------------------------

total_sales = filtered_df["sales"].sum()

total_orders = filtered_df["order_id"].nunique()

avg_order_value = (
    total_sales / total_orders
    if total_orders != 0
    else 0
)

best_year_row = (
    yearly_sales
    .sort_values("sales", ascending=False)
    .iloc[0]
)

growth_data = (
    yearly_sales
    .dropna(subset=["sales_growth_pct"])
)

if not growth_data.empty:

    best_growth_row = (
        growth_data
        .sort_values(
            "sales_growth_pct",
            ascending=False
        )
        .iloc[0]
    )

    best_growth_year = int(
        best_growth_row["order_year"]
    )

    best_growth_value = (
        best_growth_row["sales_growth_pct"]
    )

else:

    best_growth_year = None
    best_growth_value = None


best_month_row = (
    monthly_sales
    .sort_values("sales", ascending=False)
    .iloc[0]
)


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Sales",
    f"${total_sales:,.0f}"
)

col2.metric(
    "Highest Sales Year",
    int(best_year_row["order_year"]),
    f"${best_year_row['sales']:,.0f}"
)

if best_growth_year is not None:

    col3.metric(
        "Highest YoY Growth",
        f"{best_growth_value:.1f}%",
        str(best_growth_year)
    )

else:

    col3.metric(
        "Highest YoY Growth",
        "N/A"
    )

col4.metric(
    "Average Order Value",
    f"${avg_order_value:,.0f}"
)


st.divider()


# --------------------------------------------------
# SALES TREND
# --------------------------------------------------

fig_monthly = px.line(
    monthly_sales,
    x="date",
    y="sales",
    markers=True,
    title="Monthly Sales Trend"
)

fig_monthly.update_layout(
    xaxis_title="Month",
    yaxis_title="Sales ($)"
)

st.plotly_chart(
    fig_monthly,
    width="stretch"
)


# --------------------------------------------------
# YEARLY SALES AND GROWTH
# --------------------------------------------------

left, right = st.columns(2)


with left:

    fig_yearly = px.bar(
        yearly_sales,
        x="order_year",
        y="sales",
        text_auto=".2s",
        title="Annual Sales Performance"
    )

    fig_yearly.update_layout(
        xaxis_title="Year",
        yaxis_title="Sales ($)"
    )

    st.plotly_chart(
        fig_yearly,
        width="stretch"
    )


with right:

    fig_growth = px.bar(
        yearly_sales.dropna(
            subset=["sales_growth_pct"]
        ),
        x="order_year",
        y="sales_growth_pct",
        text_auto=".1f",
        title="Year-on-Year Sales Growth"
    )

    fig_growth.update_layout(
        xaxis_title="Year",
        yaxis_title="Growth (%)"
    )

    st.plotly_chart(
        fig_growth,
        width="stretch"
    )


# --------------------------------------------------
# QUARTERLY PERFORMANCE
# --------------------------------------------------

quarterly_sales = (
    filtered_df
    .groupby(
        ["order_year", "order_quarter"],
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        orders=("order_id", "nunique")
    )
)


fig_quarter = px.bar(
    quarterly_sales,
    x="order_quarter",
    y="sales",
    color="order_year",
    barmode="group",
    title="Quarterly Sales Performance"
)

fig_quarter.update_layout(
    xaxis_title="Quarter",
    yaxis_title="Sales ($)"
)

st.plotly_chart(
    fig_quarter,
    width="stretch"
)


# --------------------------------------------------
# MONTHLY SEASONALITY
# --------------------------------------------------

seasonality = (
    filtered_df
    .groupby(
        ["order_month_num", "order_month"],
        as_index=False
    )
    .agg(
        sales=("sales", "sum")
    )
    .sort_values("order_month_num")
)


fig_seasonality = px.bar(
    seasonality,
    x="order_month",
    y="sales",
    text_auto=".2s",
    title="Monthly Sales Seasonality"
)

fig_seasonality.update_layout(
    xaxis_title="Month",
    yaxis_title="Total Sales ($)"
)

st.plotly_chart(
    fig_seasonality,
    width="stretch"
)


# --------------------------------------------------
# REGION AND CATEGORY CONTRIBUTION
# --------------------------------------------------

left, right = st.columns(2)


with left:

    region_sales = (
        filtered_df
        .groupby("region", as_index=False)
        .agg(
            sales=("sales", "sum"),
            orders=("order_id", "nunique")
        )
        .sort_values(
            "sales",
            ascending=False
        )
    )

    fig_region = px.bar(
        region_sales,
        x="region",
        y="sales",
        text_auto=".2s",
        title="Sales by Region"
    )

    st.plotly_chart(
        fig_region,
        width="stretch"
    )


with right:

    category_sales = (
        filtered_df
        .groupby("category", as_index=False)
        .agg(
            sales=("sales", "sum"),
            orders=("order_id", "nunique")
        )
        .sort_values(
            "sales",
            ascending=False
        )
    )

    fig_category = px.bar(
        category_sales,
        x="category",
        y="sales",
        text_auto=".2s",
        title="Sales by Category"
    )

    st.plotly_chart(
        fig_category,
        width="stretch"
    )


# --------------------------------------------------
# CUSTOMER SEGMENT SALES
# --------------------------------------------------

segment_sales = (
    filtered_df
    .groupby("segment", as_index=False)
    .agg(
        sales=("sales", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique")
    )
    .sort_values(
        "sales",
        ascending=False
    )
)


fig_segment = px.bar(
    segment_sales,
    x="segment",
    y="sales",
    text_auto=".2s",
    title="Sales by Customer Segment"
)

st.plotly_chart(
    fig_segment,
    width="stretch"
)


# --------------------------------------------------
# SALES CONTRIBUTION %
# --------------------------------------------------

region_sales["sales_share_pct"] = (
    region_sales["sales"]
    / region_sales["sales"].sum()
    * 100
)

category_sales["sales_share_pct"] = (
    category_sales["sales"]
    / category_sales["sales"].sum()
    * 100
)


left, right = st.columns(2)


with left:

    fig_region_share = px.pie(
        region_sales,
        values="sales",
        names="region",
        title="Regional Revenue Contribution"
    )

    st.plotly_chart(
        fig_region_share,
        width="stretch"
    )


with right:

    fig_category_share = px.pie(
        category_sales,
        values="sales",
        names="category",
        title="Category Revenue Contribution"
    )

    st.plotly_chart(
        fig_category_share,
        width="stretch"
    )


# --------------------------------------------------
# DYNAMIC SALES INSIGHTS
# --------------------------------------------------

st.divider()

st.subheader("Sales Performance Insights")


best_region = (
    region_sales
    .sort_values(
        "sales",
        ascending=False
    )
    .iloc[0]
)

lowest_region = (
    region_sales
    .sort_values("sales")
    .iloc[0]
)

best_category = (
    category_sales
    .sort_values(
        "sales",
        ascending=False
    )
    .iloc[0]
)

best_segment = (
    segment_sales
    .sort_values(
        "sales",
        ascending=False
    )
    .iloc[0]
)

best_month = (
    seasonality
    .sort_values(
        "sales",
        ascending=False
    )
    .iloc[0]
)


insight_col1, insight_col2 = st.columns(2)


with insight_col1:

    st.success(
        f"""
        **Top Revenue Region**

        {best_region['region']}

        Sales: ${best_region['sales']:,.0f}

        Revenue Share:
        {best_region['sales_share_pct']:.1f}%
        """
    )

    st.success(
        f"""
        **Top Category by Sales**

        {best_category['category']}

        Sales: ${best_category['sales']:,.0f}
        """
    )

    st.success(
        f"""
        **Strongest Customer Segment**

        {best_segment['segment']}

        Sales: ${best_segment['sales']:,.0f}
        """
    )


with insight_col2:

    st.info(
        f"""
        **Strongest Sales Month**

        {best_month['order_month']}

        Combined Sales:
        ${best_month['sales']:,.0f}
        """
    )

    st.warning(
        f"""
        **Lowest Revenue Region**

        {lowest_region['region']}

        Sales:
        ${lowest_region['sales']:,.0f}
        """
    )

    if best_growth_year is not None:

        st.info(
            f"""
            **Strongest Annual Growth**

            {best_growth_year}

            YoY Growth:
            {best_growth_value:.1f}%
            """
        )


# --------------------------------------------------
# SALES MANAGEMENT SUMMARY
# --------------------------------------------------

st.subheader("Sales Management Summary")


summary_text = f"""
The selected business view generated
**${total_sales:,.0f} in sales**.

The strongest revenue year was
**{int(best_year_row['order_year'])}**,
generating **${best_year_row['sales']:,.0f}**.

**{best_region['region']}** is the leading
region by revenue, while
**{best_category['category']}** is the
highest-sales category.

The **{best_segment['segment']}**
customer segment currently contributes
the greatest sales value.

**{best_month['order_month']}** is the
strongest month when sales are aggregated
across the selected period.
"""

if best_growth_year is not None:

    summary_text += f"""

The strongest year-on-year growth occurred
in **{best_growth_year}**, when sales
increased by **{best_growth_value:.1f}%**
relative to the previous year.
"""


st.markdown(summary_text)


# --------------------------------------------------
# DETAILED SALES TABLE
# --------------------------------------------------

with st.expander(
    "View Annual Sales Data"
):

    display_yearly = yearly_sales.copy()

    display_yearly[
        "sales_growth_pct"
    ] = display_yearly[
        "sales_growth_pct"
    ].round(2)

    st.dataframe(
        display_yearly,
        width="stretch"
    )


# --------------------------------------------------
# DOWNLOAD SALES SUMMARY
# --------------------------------------------------

st.divider()

sales_csv = yearly_sales.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="Download Sales Performance Data",
    data=sales_csv,
    file_name="sales_performance_summary.csv",
    mime="text/csv"
)