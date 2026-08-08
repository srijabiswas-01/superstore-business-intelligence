import streamlit as st

from utils.theme import apply_dashboard_theme
import pandas as pd
import numpy as np
import plotly.express as px

from utils.data_loader import load_processed_data
from utils.filters import sidebar_filters


st.set_page_config(
    page_title="Geographic Analysis",
    layout="wide"
)

apply_dashboard_theme()

st.title("Geographic Analysis")

st.caption(
    "Regional, state and city performance analysis for market opportunity and risk identification"
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
# REGION SUMMARY
# --------------------------------------------------

region_summary = (
    filtered_df
    .groupby("region", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        quantity=("quantity", "sum"),
        average_discount=("discount", "mean"),
        shipping_delay=("shipping_delay", "mean")
    )
)

region_summary["profit_margin_pct"] = np.where(
    region_summary["sales"] != 0,
    region_summary["profit"]
    / region_summary["sales"]
    * 100,
    0
)

region_summary["sales_share_pct"] = (
    region_summary["sales"]
    / region_summary["sales"].sum()
    * 100
)


# --------------------------------------------------
# STATE SUMMARY
# --------------------------------------------------

state_summary = (
    filtered_df
    .groupby(
        ["state", "region"],
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        quantity=("quantity", "sum"),
        average_discount=("discount", "mean"),
        shipping_delay=("shipping_delay", "mean")
    )
)

state_summary["profit_margin_pct"] = np.where(
    state_summary["sales"] != 0,
    state_summary["profit"]
    / state_summary["sales"]
    * 100,
    0
)


# --------------------------------------------------
# CITY SUMMARY
# --------------------------------------------------

city_summary = (
    filtered_df
    .groupby(
        ["city", "state", "region"],
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        quantity=("quantity", "sum"),
        average_discount=("discount", "mean"),
        shipping_delay=("shipping_delay", "mean")
    )
)

city_summary["profit_margin_pct"] = np.where(
    city_summary["sales"] != 0,
    city_summary["profit"]
    / city_summary["sales"]
    * 100,
    0
)


# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------

best_region = (
    region_summary
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)

top_sales_region = (
    region_summary
    .sort_values(
        "sales",
        ascending=False
    )
    .iloc[0]
)

worst_region = (
    region_summary
    .sort_values("profit")
    .iloc[0]
)

best_state = (
    state_summary
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)

worst_state = (
    state_summary
    .sort_values("profit")
    .iloc[0]
)

best_city = (
    city_summary
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)

worst_city = (
    city_summary
    .sort_values("profit")
    .iloc[0]
)

loss_states = state_summary[
    state_summary["profit"] < 0
]

loss_cities = city_summary[
    city_summary["profit"] < 0
]


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Best Region by Profit",
    best_region["region"],
    f"${best_region['profit']:,.0f}"
)

col2.metric(
    "Top Sales Region",
    top_sales_region["region"],
    f"${top_sales_region['sales']:,.0f}"
)

col3.metric(
    "Best State",
    best_state["state"],
    f"${best_state['profit']:,.0f}"
)

col4.metric(
    "Best City",
    best_city["city"],
    f"${best_city['profit']:,.0f}"
)


col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "Loss-Making States",
    f"{len(loss_states):,}"
)

col6.metric(
    "Loss-Making Cities",
    f"{len(loss_cities):,}"
)

col7.metric(
    "Worst State Profit",
    f"${worst_state['profit']:,.0f}"
)

col8.metric(
    "Worst City Profit",
    f"${worst_city['profit']:,.0f}"
)


st.divider()


# --------------------------------------------------
# REGION PERFORMANCE
# --------------------------------------------------

st.subheader("Regional Performance")


left, right = st.columns(2)


with left:

    fig_region_sales = px.bar(
        region_summary.sort_values(
            "sales",
            ascending=False
        ),
        x="region",
        y="sales",
        text_auto=".2s",
        title="Sales by Region"
    )

    st.plotly_chart(
        fig_region_sales,
        width="stretch"
    )


with right:

    fig_region_profit = px.bar(
        region_summary.sort_values(
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
# REGION SALES VS PROFIT MATRIX
# --------------------------------------------------

fig_region_matrix = px.scatter(
    region_summary,
    x="sales",
    y="profit",
    size="orders",
    color="region",
    hover_name="region",
    hover_data=[
        "profit_margin_pct",
        "sales_share_pct",
        "average_discount",
        "shipping_delay"
    ],
    title="Regional Sales vs Profit Matrix"
)

st.plotly_chart(
    fig_region_matrix,
    width="stretch"
)


# --------------------------------------------------
# REGION PROFIT MARGIN
# --------------------------------------------------

fig_region_margin = px.bar(
    region_summary.sort_values(
        "profit_margin_pct",
        ascending=False
    ),
    x="region",
    y="profit_margin_pct",
    text_auto=".1f",
    title="Profit Margin by Region"
)

st.plotly_chart(
    fig_region_margin,
    width="stretch"
)


# --------------------------------------------------
# STATE PERFORMANCE
# --------------------------------------------------

st.subheader("State Performance")


left, right = st.columns(2)


with left:

    top_states_sales = (
        state_summary
        .nlargest(
            15,
            "sales"
        )
        .sort_values("sales")
    )

    fig_state_sales = px.bar(
        top_states_sales,
        x="sales",
        y="state",
        orientation="h",
        color="region",
        title="Top 15 States by Sales"
    )

    st.plotly_chart(
        fig_state_sales,
        width="stretch"
    )


with right:

    top_states_profit = (
        state_summary
        .nlargest(
            15,
            "profit"
        )
        .sort_values("profit")
    )

    fig_state_profit = px.bar(
        top_states_profit,
        x="profit",
        y="state",
        orientation="h",
        color="region",
        title="Top 15 States by Profit"
    )

    st.plotly_chart(
        fig_state_profit,
        width="stretch"
    )


# --------------------------------------------------
# LOSS-MAKING STATES
# --------------------------------------------------

st.subheader("Loss-Making States")


if not loss_states.empty:

    loss_states_sorted = (
        loss_states
        .sort_values("profit")
    )

    fig_loss_states = px.bar(
        loss_states_sorted,
        x="profit",
        y="state",
        orientation="h",
        color="region",
        title="States Generating Negative Profit"
    )

    st.plotly_chart(
        fig_loss_states,
        width="stretch"
    )

    st.error(
        f"{len(loss_states)} states generate negative aggregate profit "
        "within the selected filters."
    )

else:

    st.success(
        "No state generates negative aggregate profit under the current filters."
    )


# --------------------------------------------------
# STATE SALES VS PROFIT MATRIX
# --------------------------------------------------

st.subheader("State Opportunity and Risk Matrix")


state_sales_median = state_summary["sales"].median()
state_profit_median = state_summary["profit"].median()


def classify_state(row):
    """Assign a state to a sales/profit market group using active medians."""

    if (
        row["sales"] >= state_sales_median
        and row["profit"] >= state_profit_median
    ):
        return "Strong Market"

    elif (
        row["sales"] >= state_sales_median
        and row["profit"] < state_profit_median
    ):
        return "Margin Risk"

    elif (
        row["sales"] < state_sales_median
        and row["profit"] >= state_profit_median
    ):
        return "Growth Opportunity"

    else:
        return "Low Performance"


state_summary["market_group"] = (
    state_summary.apply(
        classify_state,
        axis=1
    )
)


fig_state_matrix = px.scatter(
    state_summary,
    x="sales",
    y="profit",
    size="orders",
    color="market_group",
    hover_name="state",
    hover_data=[
        "region",
        "profit_margin_pct",
        "average_discount",
        "customers"
    ],
    title="State Sales vs Profit Strategic Matrix"
)

fig_state_matrix.add_vline(
    x=state_sales_median,
    line_dash="dash"
)

fig_state_matrix.add_hline(
    y=state_profit_median,
    line_dash="dash"
)

st.plotly_chart(
    fig_state_matrix,
    width="stretch"
)


# --------------------------------------------------
# CITY ANALYSIS
# --------------------------------------------------

st.subheader("City Performance")


left, right = st.columns(2)


with left:

    top_cities_sales = (
        city_summary
        .nlargest(
            15,
            "sales"
        )
        .sort_values("sales")
    )

    fig_city_sales = px.bar(
        top_cities_sales,
        x="sales",
        y="city",
        orientation="h",
        color="region",
        hover_data=["state"],
        title="Top 15 Cities by Sales"
    )

    st.plotly_chart(
        fig_city_sales,
        width="stretch"
    )


with right:

    top_cities_profit = (
        city_summary
        .nlargest(
            15,
            "profit"
        )
        .sort_values("profit")
    )

    fig_city_profit = px.bar(
        top_cities_profit,
        x="profit",
        y="city",
        orientation="h",
        color="region",
        hover_data=["state"],
        title="Top 15 Cities by Profit"
    )

    st.plotly_chart(
        fig_city_profit,
        width="stretch"
    )


# --------------------------------------------------
# LOSS-MAKING CITIES
# --------------------------------------------------

if not loss_cities.empty:

    worst_cities = (
        loss_cities
        .nsmallest(
            20,
            "profit"
        )
        .sort_values("profit")
    )

    fig_loss_cities = px.bar(
        worst_cities,
        x="profit",
        y="city",
        orientation="h",
        color="region",
        hover_data=["state"],
        title="Largest City-Level Losses"
    )

    st.plotly_chart(
        fig_loss_cities,
        width="stretch"
    )


# --------------------------------------------------
# OPTIONAL US STATE MAP
# --------------------------------------------------

st.subheader("US State Performance Map")

st.caption(
    "The map uses state abbreviations. If the source dataset does not contain state codes, they are generated from a lookup."
)


state_to_code = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY"
}


state_map_data = state_summary.copy()

state_map_data["state_code"] = (
    state_map_data["state"]
    .map(state_to_code)
)

state_map_data = state_map_data.dropna(
    subset=["state_code"]
)


map_metric = st.radio(
    "Map Metric",
    [
        "Sales",
        "Profit",
        "Profit Margin"
    ],
    horizontal=True
)


if map_metric == "Sales":

    map_column = "sales"
    map_title = "Sales by State"

elif map_metric == "Profit":

    map_column = "profit"
    map_title = "Profit by State"

else:

    map_column = "profit_margin_pct"
    map_title = "Profit Margin by State"


fig_map = px.choropleth(
    state_map_data,
    locations="state_code",
    locationmode="USA-states",
    color=map_column,
    scope="usa",
    hover_name="state",
    hover_data=[
        "sales",
        "profit",
        "profit_margin_pct",
        "orders",
        "customers"
    ],
    title=map_title
)

fig_map.update_layout(
    geo_scope="usa"
)

st.plotly_chart(
    fig_map,
    width="stretch"
)


# --------------------------------------------------
# REGIONAL REVENUE CONTRIBUTION
# --------------------------------------------------

fig_region_share = px.pie(
    region_summary,
    values="sales",
    names="region",
    title="Regional Revenue Contribution"
)

st.plotly_chart(
    fig_region_share,
    width="stretch"
)


# --------------------------------------------------
# GEOGRAPHIC BUSINESS INSIGHTS
# --------------------------------------------------

st.divider()

st.subheader("Geographic Business Insights")


best_margin_region = (
    region_summary
    .sort_values(
        "profit_margin_pct",
        ascending=False
    )
    .iloc[0]
)

largest_sales_state = (
    state_summary
    .sort_values(
        "sales",
        ascending=False
    )
    .iloc[0]
)

largest_sales_city = (
    city_summary
    .sort_values(
        "sales",
        ascending=False
    )
    .iloc[0]
)


insight1, insight2 = st.columns(2)


with insight1:

    st.success(
        f"""
        **Strongest Region by Profit**

        {best_region['region']}

        Sales: ${best_region['sales']:,.0f}

        Profit: ${best_region['profit']:,.0f}

        Margin: {best_region['profit_margin_pct']:.1f}%
        """
    )

    st.success(
        f"""
        **Highest-Margin Region**

        {best_margin_region['region']}

        Margin: {best_margin_region['profit_margin_pct']:.1f}%
        """
    )

    st.success(
        f"""
        **Highest-Sales State**

        {largest_sales_state['state']}

        Sales: ${largest_sales_state['sales']:,.0f}
        """
    )


with insight2:

    if worst_region["profit"] < 0:

        st.error(
            f"""
            **Regional Risk**

            {worst_region['region']}

            Profit: ${worst_region['profit']:,.0f}

            Margin: {worst_region['profit_margin_pct']:.1f}%
            """
        )

    else:

        st.warning(
            f"""
            **Lowest-Profit Region**

            {worst_region['region']}

            Profit: ${worst_region['profit']:,.0f}
            """
        )

    st.error(
        f"""
        **Weakest State**

        {worst_state['state']}

        Region: {worst_state['region']}

        Profit: ${worst_state['profit']:,.0f}
        """
    )

    st.error(
        f"""
        **Largest City-Level Loss**

        {worst_city['city']}, {worst_city['state']}

        Profit: ${worst_city['profit']:,.0f}
        """
    )


# --------------------------------------------------
# GROWTH OPPORTUNITIES
# --------------------------------------------------

st.subheader("Geographic Growth Opportunities")


growth_states = (
    state_summary[
        state_summary[
            "market_group"
        ]
        == "Growth Opportunity"
    ]
    .sort_values(
        "profit_margin_pct",
        ascending=False
    )
)


if not growth_states.empty:

    st.success(
        f"{len(growth_states)} states are classified as potential geographic growth opportunities."
    )

    st.dataframe(
        growth_states[
            [
                "state",
                "region",
                "sales",
                "profit",
                "profit_margin_pct",
                "orders",
                "customers"
            ]
        ],
        width="stretch"
    )

else:

    st.info(
        "No states currently meet the growth-opportunity classification."
    )


# --------------------------------------------------
# MARGIN-RISK STATES
# --------------------------------------------------

st.subheader("Geographic Margin Risks")


margin_risk_states = (
    state_summary[
        state_summary[
            "market_group"
        ]
        == "Margin Risk"
    ]
    .sort_values(
        "sales",
        ascending=False
    )
)


if not margin_risk_states.empty:

    st.warning(
        f"{len(margin_risk_states)} states have relatively strong sales "
        "but weaker profitability."
    )

    st.dataframe(
        margin_risk_states[
            [
                "state",
                "region",
                "sales",
                "profit",
                "profit_margin_pct",
                "average_discount"
            ]
        ],
        width="stretch"
    )

else:

    st.success(
        "No clear geographic margin-risk states were identified."
    )


# --------------------------------------------------
# MANAGEMENT RECOMMENDATIONS
# --------------------------------------------------

st.subheader("Geographic Management Recommendations")


st.success(
    f"""
    **Protect the strongest regional market:**  
    {best_region['region']} currently produces the greatest regional profit contribution.
    Management should identify which products, states and customer segments are supporting
    this performance and assess whether those patterns can be replicated elsewhere.
    """
)


if not growth_states.empty:

    st.info(
        """
        **Evaluate growth markets:**  
        Growth-opportunity states combine relatively lower sales with comparatively
        stronger profitability. These markets may justify targeted commercial investment.
        """
    )


if not margin_risk_states.empty:

    st.warning(
        """
        **Review high-sales/weak-profit markets:**  
        Margin-risk states should be investigated for discount exposure,
        product mix and transaction economics before additional expansion.
        """
    )


if not loss_states.empty:

    st.error(
        f"""
        **Investigate loss-making states:**  
        {len(loss_states)} states currently generate negative aggregate profit.
        Management should review whether losses are concentrated in particular
        products, sub-categories, customer segments or discount levels.
        """
    )


st.info(
    """
    Geographic results should be interpreted together with the Product,
    Discount and Customer Intelligence pages before making market-entry,
    expansion or withdrawal decisions.
    """
)


# --------------------------------------------------
# DETAILED TABLES
# --------------------------------------------------

with st.expander(
    "View Region Performance Data"
):

    st.dataframe(
        region_summary.sort_values(
            "profit",
            ascending=False
        ),
        width="stretch"
    )


with st.expander(
    "View State Performance Data"
):

    st.dataframe(
        state_summary.sort_values(
            "profit",
            ascending=False
        ),
        width="stretch"
    )


with st.expander(
    "View City Performance Data"
):

    st.dataframe(
        city_summary.sort_values(
            "profit",
            ascending=False
        ),
        width="stretch"
    )


# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------

st.divider()

state_csv = (
    state_summary
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    label="Download State Performance Data",
    data=state_csv,
    file_name="geographic_state_analysis.csv",
    mime="text/csv"
)


city_csv = (
    city_summary
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    label="Download City Performance Data",
    data=city_csv,
    file_name="geographic_city_analysis.csv",
    mime="text/csv"
)
