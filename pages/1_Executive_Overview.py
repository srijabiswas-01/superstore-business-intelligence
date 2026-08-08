import streamlit as st

from utils.theme import apply_dashboard_theme
import plotly.express as px
import pandas as pd

from utils.data_loader import load_processed_data
from utils.filters import sidebar_filters
from utils.kpi_engine import calculate_kpis


st.set_page_config(
    page_title="Executive Overview",
    layout="wide"
)

apply_dashboard_theme()

st.title("Executive Overview")

st.caption(
    "High-level view of sales, profitability, customers and business performance"
)

df = load_processed_data()
filtered_df = sidebar_filters(df)

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()

kpis = calculate_kpis(filtered_df)


# -----------------------------
# KPI CARDS
# -----------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Sales",
    f"${kpis['total_sales']:,.0f}"
)

col2.metric(
    "Total Profit",
    f"${kpis['total_profit']:,.0f}"
)

col3.metric(
    "Profit Margin",
    f"{kpis['profit_margin']:.1f}%"
)

col4.metric(
    "Orders",
    f"{kpis['orders']:,}"
)


col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "Customers",
    f"{kpis['customers']:,}"
)

col6.metric(
    "Average Order Value",
    f"${kpis['average_order_value']:,.0f}"
)

col7.metric(
    "Average Discount",
    f"{kpis['average_discount']:.1f}%"
)

col8.metric(
    "Shipping Delay",
    f"{kpis['shipping_delay']:.1f} days"
)


st.divider()


# -----------------------------
# MONTHLY SALES AND PROFIT TREND
# -----------------------------

monthly = (
    filtered_df
    .groupby("year_month", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum")
    )
)

monthly["date"] = pd.to_datetime(monthly["year_month"])


fig_trend = px.line(
    monthly,
    x="date",
    y=["sales", "profit"],
    markers=True,
    title="Sales and Profit Trend Over Time"
)

fig_trend.update_layout(
    xaxis_title="Date",
    yaxis_title="Value",
    legend_title="Metric"
)

st.plotly_chart(
    fig_trend,
    width="stretch"
)


# -----------------------------
# CATEGORY AND REGION
# -----------------------------

left, right = st.columns(2)


with left:

    category_summary = (
        filtered_df
        .groupby("category", as_index=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum")
        )
    )

    fig_category = px.bar(
        category_summary,
        x="category",
        y=["sales", "profit"],
        barmode="group",
        title="Category Sales and Profit"
    )

    st.plotly_chart(
        fig_category,
        width="stretch"
    )


with right:

    region_summary = (
        filtered_df
        .groupby("region", as_index=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique")
        )
    )

    fig_region = px.scatter(
        region_summary,
        x="sales",
        y="profit",
        size="orders",
        color="region",
        hover_name="region",
        title="Regional Sales vs Profit"
    )

    st.plotly_chart(
        fig_region,
        width="stretch"
    )


# -----------------------------
# YEARLY PERFORMANCE
# -----------------------------

yearly = (
    filtered_df
    .groupby("order_year", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum")
    )
    .sort_values("order_year")
)

yearly["sales_growth_pct"] = (
    yearly["sales"]
    .pct_change()
    * 100
)

yearly["profit_growth_pct"] = (
    yearly["profit"]
    .pct_change()
    * 100
)


fig_growth = px.bar(
    yearly,
    x="order_year",
    y="sales_growth_pct",
    title="Year-on-Year Sales Growth"
)

fig_growth.update_layout(
    xaxis_title="Year",
    yaxis_title="Sales Growth %"
)

st.plotly_chart(
    fig_growth,
    width="stretch"
)


# -----------------------------
# TOP AND BOTTOM PRODUCTS
# -----------------------------

product_summary = (
    filtered_df
    .groupby("product_name", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum")
    )
)

left, right = st.columns(2)


with left:

    top_products = (
        product_summary
        .nlargest(10, "profit")
        .sort_values("profit")
    )

    fig_top = px.bar(
        top_products,
        x="profit",
        y="product_name",
        orientation="h",
        title="Top 10 Products by Profit"
    )

    st.plotly_chart(
        fig_top,
        width="stretch"
    )


with right:

    worst_products = (
        product_summary
        .nsmallest(10, "profit")
        .sort_values("profit")
    )

    fig_worst = px.bar(
        worst_products,
        x="profit",
        y="product_name",
        orientation="h",
        title="Bottom 10 Products by Profit"
    )

    st.plotly_chart(
        fig_worst,
        width="stretch"
    )


# -----------------------------
# DYNAMIC BUSINESS INSIGHTS
# -----------------------------

st.divider()

st.subheader("Dynamic Business Insights")


best_region = (
    region_summary
    .sort_values("profit", ascending=False)
    .iloc[0]
)

worst_region = (
    region_summary
    .sort_values("profit")
    .iloc[0]
)


best_category = (
    category_summary
    .sort_values("profit", ascending=False)
    .iloc[0]
)

worst_category = (
    category_summary
    .sort_values("profit")
    .iloc[0]
)


best_product = (
    product_summary
    .sort_values("profit", ascending=False)
    .iloc[0]
)

worst_product = (
    product_summary
    .sort_values("profit")
    .iloc[0]
)


insight1, insight2 = st.columns(2)


with insight1:

    st.success(
        f"""
        **Strongest Region:** {best_region['region']}

        Profit: ${best_region['profit']:,.0f}

        Sales: ${best_region['sales']:,.0f}
        """
    )

    st.success(
        f"""
        **Strongest Category:** {best_category['category']}

        Profit: ${best_category['profit']:,.0f}
        """
    )

    st.success(
        f"""
        **Most Profitable Product**

        {best_product['product_name']}

        Profit: ${best_product['profit']:,.0f}
        """
    )


with insight2:

    if worst_region["profit"] < 0:

        st.error(
            f"""
            **Region Requiring Attention:** {worst_region['region']}

            Profit: ${worst_region['profit']:,.0f}
            """
        )

    else:

        st.warning(
            f"""
            **Lowest Profit Region:** {worst_region['region']}

            Profit: ${worst_region['profit']:,.0f}
            """
        )


    if worst_category["profit"] < 0:

        st.error(
            f"""
            **Category Risk:** {worst_category['category']}

            Profit: ${worst_category['profit']:,.0f}
            """
        )

    else:

        st.warning(
            f"""
            **Lowest Profit Category:** {worst_category['category']}

            Profit: ${worst_category['profit']:,.0f}
            """
        )


    st.error(
        f"""
        **Largest Product Loss**

        {worst_product['product_name']}

        Profit: ${worst_product['profit']:,.0f}
        """
    )


# -----------------------------
# MANAGEMENT SUMMARY
# -----------------------------

st.subheader("Management Summary")

st.markdown(
    f"""
    The selected business view generated **${kpis['total_sales']:,.0f}**
    in total sales and **${kpis['total_profit']:,.0f}** in profit,
    producing a profit margin of **{kpis['profit_margin']:.1f}%**.

    **{best_region['region']}** is currently the strongest region by profit,
    while **{best_category['category']}** is the strongest category.

    Management should closely review
    **{worst_product['product_name']}**, which is currently the
    largest product-level loss contributor within the selected filters.
    """
)


# -----------------------------
# DOWNLOAD FILTERED DATA
# -----------------------------

st.divider()

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data",
    data=csv,
    file_name="filtered_superstore_data.csv",
    mime="text/csv"
)