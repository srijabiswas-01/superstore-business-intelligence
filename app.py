import streamlit as st

from utils.theme import apply_dashboard_theme

from utils.data_loader import load_processed_data
from utils.kpi_engine import calculate_kpis
from utils.filters import sidebar_filters


st.set_page_config(
    page_title="Superstore Business Intelligence",
    layout="wide"
)

apply_dashboard_theme()

st.title(
    "Superstore Business Intelligence Platform"
)

st.caption(
    "Executive Analytics | Predictive Modelling | AI Business Insights"
)

try:
    df = load_processed_data()

    filtered_df = sidebar_filters(df)

    kpis = calculate_kpis(filtered_df)

    st.success(
        f"Dataset loaded successfully: {len(filtered_df):,} records"
    )

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
        "Avg Shipping Delay",
        f"{kpis['shipping_delay']:.1f} days"
    )

    st.subheader("Processed Dataset Preview")

    st.dataframe(
        filtered_df.head(100),
        width="stretch"
    )

except Exception as e:
    st.error(str(e))