import streamlit as st

from utils.theme import apply_dashboard_theme
import pandas as pd
import numpy as np
import plotly.express as px

from utils.data_loader import load_processed_data
from utils.filters import sidebar_filters


st.set_page_config(
    page_title="Customer Intelligence",
    layout="wide"
)

apply_dashboard_theme()

st.title("Customer Intelligence")

st.caption(
    "Customer value, repeat purchasing, segment performance and RFM analysis"
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
# CUSTOMER-LEVEL SUMMARY
# --------------------------------------------------

latest_date = filtered_df["order_date"].max()

customer_summary = (
    filtered_df
    .groupby(
        [
            "customer_id",
            "customer_name",
            "segment"
        ],
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        quantity=("quantity", "sum"),
        average_discount=("discount", "mean"),
        first_order=("order_date", "min"),
        last_order=("order_date", "max")
    )
)

customer_summary["average_order_value"] = np.where(
    customer_summary["orders"] != 0,
    customer_summary["sales"]
    / customer_summary["orders"],
    0
)

customer_summary["profit_margin_pct"] = np.where(
    customer_summary["sales"] != 0,
    customer_summary["profit"]
    / customer_summary["sales"]
    * 100,
    0
)

customer_summary["recency_days"] = (
    latest_date
    - customer_summary["last_order"]
).dt.days

customer_summary["customer_status"] = np.where(
    customer_summary["orders"] > 1,
    "Repeat Customer",
    "Single-Order Customer"
)


# --------------------------------------------------
# CUSTOMER KPIs
# --------------------------------------------------

total_customers = customer_summary["customer_id"].nunique()

repeat_customers = (
    customer_summary[
        customer_summary["orders"] > 1
    ]["customer_id"]
    .nunique()
)

single_order_customers = (
    customer_summary[
        customer_summary["orders"] == 1
    ]["customer_id"]
    .nunique()
)

repeat_rate = (
    repeat_customers
    / total_customers
    * 100
    if total_customers != 0
    else 0
)

sales_per_customer = (
    customer_summary["sales"].sum()
    / total_customers
    if total_customers != 0
    else 0
)

profit_per_customer = (
    customer_summary["profit"].sum()
    / total_customers
    if total_customers != 0
    else 0
)

best_customer = (
    customer_summary
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)

highest_sales_customer = (
    customer_summary
    .sort_values(
        "sales",
        ascending=False
    )
    .iloc[0]
)

worst_customer = (
    customer_summary
    .sort_values("profit")
    .iloc[0]
)


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Customers",
    f"{total_customers:,}"
)

col2.metric(
    "Repeat Customers",
    f"{repeat_customers:,}"
)

col3.metric(
    "Repeat Customer Rate",
    f"{repeat_rate:.1f}%"
)

col4.metric(
    "Single-Order Customers",
    f"{single_order_customers:,}"
)


col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "Sales per Customer",
    f"${sales_per_customer:,.0f}"
)

col6.metric(
    "Profit per Customer",
    f"${profit_per_customer:,.0f}"
)

col7.metric(
    "Highest Customer Sales",
    f"${highest_sales_customer['sales']:,.0f}"
)

col8.metric(
    "Highest Customer Profit",
    f"${best_customer['profit']:,.0f}"
)


st.divider()


# --------------------------------------------------
# CUSTOMER SEGMENT PERFORMANCE
# --------------------------------------------------

segment_summary = (
    filtered_df
    .groupby(
        "segment",
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

segment_summary["profit_margin_pct"] = np.where(
    segment_summary["sales"] != 0,
    segment_summary["profit"]
    / segment_summary["sales"]
    * 100,
    0
)

segment_summary["sales_per_customer"] = np.where(
    segment_summary["customers"] != 0,
    segment_summary["sales"]
    / segment_summary["customers"],
    0
)

segment_summary["profit_per_customer"] = np.where(
    segment_summary["customers"] != 0,
    segment_summary["profit"]
    / segment_summary["customers"],
    0
)


left, right = st.columns(2)


with left:

    fig_segment_sales = px.bar(
        segment_summary.sort_values(
            "sales",
            ascending=False
        ),
        x="segment",
        y="sales",
        text_auto=".2s",
        title="Sales by Customer Segment"
    )

    st.plotly_chart(
        fig_segment_sales,
        width="stretch"
    )


with right:

    fig_segment_profit = px.bar(
        segment_summary.sort_values(
            "profit",
            ascending=False
        ),
        x="segment",
        y="profit",
        text_auto=".2s",
        title="Profit by Customer Segment"
    )

    st.plotly_chart(
        fig_segment_profit,
        width="stretch"
    )


# --------------------------------------------------
# SEGMENT PROFITABILITY MATRIX
# --------------------------------------------------

fig_segment_matrix = px.scatter(
    segment_summary,
    x="sales",
    y="profit",
    size="customers",
    color="segment",
    hover_name="segment",
    hover_data=[
        "profit_margin_pct",
        "sales_per_customer",
        "profit_per_customer",
        "average_discount"
    ],
    title="Customer Segment Sales vs Profit"
)

st.plotly_chart(
    fig_segment_matrix,
    width="stretch"
)


# --------------------------------------------------
# TOP CUSTOMERS
# --------------------------------------------------

st.subheader("High-Value Customers")


left, right = st.columns(2)


with left:

    top_sales_customers = (
        customer_summary
        .nlargest(
            15,
            "sales"
        )
        .sort_values("sales")
    )

    fig_top_sales_customer = px.bar(
        top_sales_customers,
        x="sales",
        y="customer_name",
        orientation="h",
        color="segment",
        title="Top 15 Customers by Sales"
    )

    st.plotly_chart(
        fig_top_sales_customer,
        width="stretch"
    )


with right:

    top_profit_customers = (
        customer_summary
        .nlargest(
            15,
            "profit"
        )
        .sort_values("profit")
    )

    fig_top_profit_customer = px.bar(
        top_profit_customers,
        x="profit",
        y="customer_name",
        orientation="h",
        color="segment",
        title="Top 15 Customers by Profit"
    )

    st.plotly_chart(
        fig_top_profit_customer,
        width="stretch"
    )


# --------------------------------------------------
# LOSS-MAKING CUSTOMERS
# --------------------------------------------------

st.subheader("Loss-Making Customers")


loss_customers = (
    customer_summary[
        customer_summary["profit"] < 0
    ]
    .sort_values("profit")
)


if not loss_customers.empty:

    st.error(
        f"{len(loss_customers):,} customers generate negative aggregate profit "
        "within the selected filters."
    )

    fig_loss_customers = px.bar(
        loss_customers.head(20),
        x="profit",
        y="customer_name",
        orientation="h",
        color="segment",
        title="Largest Customer-Level Losses"
    )

    st.plotly_chart(
        fig_loss_customers,
        width="stretch"
    )

    with st.expander(
        "View Loss-Making Customer Table"
    ):

        st.dataframe(
            loss_customers[
                [
                    "customer_name",
                    "segment",
                    "sales",
                    "profit",
                    "profit_margin_pct",
                    "orders",
                    "average_discount"
                ]
            ],
            width="stretch"
        )

else:

    st.success(
        "No customers generate negative aggregate profit "
        "under the selected filters."
    )


# --------------------------------------------------
# REPEAT PURCHASE ANALYSIS
# --------------------------------------------------

st.subheader("Repeat Purchasing")


status_summary = (
    customer_summary
    .groupby(
        "customer_status",
        as_index=False
    )
    .agg(
        customers=("customer_id", "nunique"),
        sales=("sales", "sum"),
        profit=("profit", "sum")
    )
)


left, right = st.columns(2)


with left:

    fig_repeat = px.pie(
        status_summary,
        values="customers",
        names="customer_status",
        title="Repeat vs Single-Order Customers"
    )

    st.plotly_chart(
        fig_repeat,
        width="stretch"
    )


with right:

    fig_repeat_value = px.bar(
        status_summary,
        x="customer_status",
        y=["sales", "profit"],
        barmode="group",
        title="Value Contribution by Customer Status"
    )

    st.plotly_chart(
        fig_repeat_value,
        width="stretch"
    )


# --------------------------------------------------
# PURCHASE FREQUENCY DISTRIBUTION
# --------------------------------------------------

fig_frequency = px.histogram(
    customer_summary,
    x="orders",
    nbins=20,
    title="Customer Order Frequency Distribution"
)

fig_frequency.update_layout(
    xaxis_title="Number of Orders",
    yaxis_title="Customers"
)

st.plotly_chart(
    fig_frequency,
    width="stretch"
)


# --------------------------------------------------
# RFM ANALYSIS
# --------------------------------------------------

st.divider()

st.subheader("RFM Customer Segmentation")

st.caption(
    "RFM uses Recency, Frequency and Monetary Value to identify customer value groups."
)


rfm = customer_summary[
    [
        "customer_id",
        "customer_name",
        "segment",
        "recency_days",
        "orders",
        "sales",
        "profit"
    ]
].copy()

rfm = rfm.rename(
    columns={
        "orders": "frequency",
        "sales": "monetary"
    }
)


# --------------------------------------------------
# RFM SCORES
# --------------------------------------------------

def safe_qcut(series, labels):
    """Create four ranked quantile groups with a stable small-sample fallback.

    Ranking breaks duplicate boundaries before ``qcut``. If four quantiles still
    cannot be formed, every record receives the neutral score of two.
    """

    try:

        return pd.qcut(
            series.rank(method="first"),
            q=4,
            labels=labels
        )

    except ValueError:

        return pd.Series(
            [2] * len(series),
            index=series.index
        )


# Lower recency is better
rfm["r_score"] = safe_qcut(
    rfm["recency_days"],
    [4, 3, 2, 1]
).astype(int)

# Higher frequency is better
rfm["f_score"] = safe_qcut(
    rfm["frequency"],
    [1, 2, 3, 4]
).astype(int)

# Higher monetary is better
rfm["m_score"] = safe_qcut(
    rfm["monetary"],
    [1, 2, 3, 4]
).astype(int)


rfm["rfm_score"] = (
    rfm["r_score"]
    + rfm["f_score"]
    + rfm["m_score"]
)


# --------------------------------------------------
# RFM SEGMENT RULES
# --------------------------------------------------

def classify_rfm(row):
    """Map recency, frequency, and monetary scores to an actionable RFM segment."""

    if (
        row["r_score"] >= 4
        and row["f_score"] >= 3
        and row["m_score"] >= 3
    ):
        return "Champions"

    elif (
        row["f_score"] >= 3
        and row["m_score"] >= 3
    ):
        return "Loyal Customers"

    elif (
        row["r_score"] >= 3
        and row["f_score"] <= 2
    ):
        return "Potential Loyalists"

    elif (
        row["r_score"] <= 2
        and row["f_score"] >= 3
    ):
        return "At Risk"

    elif (
        row["r_score"] <= 2
        and row["m_score"] <= 2
    ):
        return "Low Value"

    else:
        return "Needs Attention"


rfm["rfm_segment"] = (
    rfm.apply(
        classify_rfm,
        axis=1
    )
)


# --------------------------------------------------
# RFM SUMMARY
# --------------------------------------------------

rfm_summary = (
    rfm
    .groupby(
        "rfm_segment",
        as_index=False
    )
    .agg(
        customers=("customer_id", "nunique"),
        sales=("monetary", "sum"),
        profit=("profit", "sum"),
        avg_recency=("recency_days", "mean"),
        avg_frequency=("frequency", "mean")
    )
    .sort_values(
        "sales",
        ascending=False
    )
)


left, right = st.columns(2)


with left:

    fig_rfm_customers = px.bar(
        rfm_summary,
        x="rfm_segment",
        y="customers",
        text_auto=True,
        title="Customers by RFM Segment"
    )

    st.plotly_chart(
        fig_rfm_customers,
        width="stretch"
    )


with right:

    fig_rfm_sales = px.bar(
        rfm_summary,
        x="rfm_segment",
        y="sales",
        text_auto=".2s",
        title="Revenue by RFM Segment"
    )

    st.plotly_chart(
        fig_rfm_sales,
        width="stretch"
    )


# --------------------------------------------------
# RFM SCATTER
# --------------------------------------------------

# Plotly marker sizes must be non-negative. Keep the signed profit column for
# hover details, and use its magnitude only to scale the bubbles.
rfm_scatter = rfm.assign(profit_magnitude=rfm["profit"].abs())

fig_rfm_scatter = px.scatter(
    rfm_scatter,
    x="frequency",
    y="monetary",
    color="rfm_segment",
    size="profit_magnitude",
    hover_name="customer_name",
    hover_data=[
        "recency_days",
        "segment",
        "profit"
    ],
    title="Customer Frequency vs Monetary Value"
)

st.plotly_chart(
    fig_rfm_scatter,
    width="stretch"
)


# --------------------------------------------------
# RFM TABLE
# --------------------------------------------------

with st.expander(
    "View RFM Customer Segmentation"
):

    st.dataframe(
        rfm.sort_values(
            "rfm_score",
            ascending=False
        ),
        width="stretch"
    )


# --------------------------------------------------
# CUSTOMER VALUE MATRIX
# --------------------------------------------------

st.subheader("Customer Value Matrix")


sales_median = customer_summary["sales"].median()
profit_median = customer_summary["profit"].median()


def classify_customer_value(row):
    """Classify a customer by sales and profit relative to active medians."""

    if (
        row["sales"] >= sales_median
        and row["profit"] >= profit_median
    ):
        return "High-Value Customer"

    elif (
        row["sales"] >= sales_median
        and row["profit"] < profit_median
    ):
        return "Revenue Strong / Margin Risk"

    elif (
        row["sales"] < sales_median
        and row["profit"] >= profit_median
    ):
        return "Growth Opportunity"

    else:
        return "Low Value / Review"


customer_summary["value_group"] = (
    customer_summary.apply(
        classify_customer_value,
        axis=1
    )
)


fig_customer_matrix = px.scatter(
    customer_summary,
    x="sales",
    y="profit",
    size="orders",
    color="value_group",
    hover_name="customer_name",
    hover_data=[
        "segment",
        "profit_margin_pct",
        "average_order_value",
        "average_discount"
    ],
    title="Customer Sales vs Profit Matrix"
)

fig_customer_matrix.add_vline(
    x=sales_median,
    line_dash="dash"
)

fig_customer_matrix.add_hline(
    y=profit_median,
    line_dash="dash"
)

st.plotly_chart(
    fig_customer_matrix,
    width="stretch"
)


# --------------------------------------------------
# DYNAMIC CUSTOMER INSIGHTS
# --------------------------------------------------

st.divider()

st.subheader("Customer Intelligence Insights")


best_segment = (
    segment_summary
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)

highest_sales_segment = (
    segment_summary
    .sort_values(
        "sales",
        ascending=False
    )
    .iloc[0]
)

best_margin_segment = (
    segment_summary
    .sort_values(
        "profit_margin_pct",
        ascending=False
    )
    .iloc[0]
)


insight1, insight2 = st.columns(2)


with insight1:

    st.success(
        f"""
        **Most Profitable Customer**

        {best_customer['customer_name']}

        Segment: {best_customer['segment']}

        Profit: ${best_customer['profit']:,.0f}

        Sales: ${best_customer['sales']:,.0f}
        """
    )

    st.success(
        f"""
        **Highest Revenue Customer**

        {highest_sales_customer['customer_name']}

        Sales: ${highest_sales_customer['sales']:,.0f}

        Profit: ${highest_sales_customer['profit']:,.0f}
        """
    )

    st.success(
        f"""
        **Most Profitable Segment**

        {best_segment['segment']}

        Profit: ${best_segment['profit']:,.0f}

        Margin: {best_segment['profit_margin_pct']:.1f}%
        """
    )


with insight2:

    if worst_customer["profit"] < 0:

        st.error(
            f"""
            **Largest Customer-Level Loss**

            {worst_customer['customer_name']}

            Segment: {worst_customer['segment']}

            Profit: ${worst_customer['profit']:,.0f}
            """
        )

    st.info(
        f"""
        **Repeat Purchasing**

        {repeat_rate:.1f}% of customers placed
        more than one unique order within the
        selected period.
        """
    )

    st.info(
        f"""
        **Best Segment Margin**

        {best_margin_segment['segment']}

        Margin: {best_margin_segment['profit_margin_pct']:.1f}%
        """
    )


# --------------------------------------------------
# RFM INSIGHTS
# --------------------------------------------------

if not rfm_summary.empty:

    largest_rfm_segment = (
        rfm_summary
        .sort_values(
            "customers",
            ascending=False
        )
        .iloc[0]
    )

    strongest_rfm_revenue = (
        rfm_summary
        .sort_values(
            "sales",
            ascending=False
        )
        .iloc[0]
    )

    st.info(
        f"""
        **RFM Customer Structure**

        The largest RFM group is
        **{largest_rfm_segment['rfm_segment']}**
        with {int(largest_rfm_segment['customers'])} customers.

        The greatest RFM revenue contribution comes from
        **{strongest_rfm_revenue['rfm_segment']}**,
        generating approximately
        **${strongest_rfm_revenue['sales']:,.0f}**.
        """
    )


# --------------------------------------------------
# MANAGEMENT RECOMMENDATIONS
# --------------------------------------------------

st.subheader("Customer Management Recommendations")


st.success(
    f"""
    **Protect high-value relationships:**  
    {best_customer['customer_name']} currently generates the greatest
    customer-level profit contribution under the selected filters.
    High-value customers should receive appropriate retention attention.
    """
)


if repeat_rate < 50:

    st.warning(
        """
        **Review repeat purchasing:**  
        Less than half of customers are repeat purchasers in the selected view.
        Management should investigate retention, follow-up and cross-selling opportunities.
        """
    )

else:

    st.info(
        """
        **Maintain repeat-customer engagement:**  
        Repeat purchasing represents a meaningful part of the current customer base.
        Retention programmes should protect these relationships.
        """
    )


if not loss_customers.empty:

    st.error(
        f"""
        **Investigate customer profitability:**  
        {len(loss_customers)} customers currently generate negative aggregate profit.
        Review their product mix, discount exposure and transaction economics
        before increasing promotional expenditure.
        """
    )


at_risk = rfm[
    rfm["rfm_segment"] == "At Risk"
]

if not at_risk.empty:

    st.warning(
        f"""
        **Retention opportunity:**  
        {len(at_risk)} customers are classified as At Risk based on
        their recency and historical purchase frequency.
        These customers may justify targeted retention activity.
        """
    )


champions = rfm[
    rfm["rfm_segment"] == "Champions"
]

if not champions.empty:

    st.success(
        f"""
        **Champion customers:**  
        {len(champions)} customers are classified as Champions.
        Management should protect these relationships and consider
        relevant loyalty, cross-selling or premium-service opportunities.
        """
    )


# --------------------------------------------------
# CUSTOMER TABLE
# --------------------------------------------------

with st.expander(
    "View Complete Customer Performance Table"
):

    st.dataframe(
        customer_summary.sort_values(
            "profit",
            ascending=False
        ),
        width="stretch"
    )


# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------

st.divider()

customer_csv = (
    customer_summary
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    label="Download Customer Intelligence Data",
    data=customer_csv,
    file_name="customer_intelligence.csv",
    mime="text/csv"
)


rfm_csv = (
    rfm
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    label="Download RFM Segmentation",
    data=rfm_csv,
    file_name="customer_rfm_segmentation.csv",
    mime="text/csv"
)
