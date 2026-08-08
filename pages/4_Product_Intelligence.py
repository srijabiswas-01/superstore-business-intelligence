import streamlit as st

from utils.theme import apply_dashboard_theme
import pandas as pd
import numpy as np
import plotly.express as px

from utils.data_loader import load_processed_data
from utils.filters import sidebar_filters


st.set_page_config(
    page_title="Product Intelligence",
    layout="wide"
)

apply_dashboard_theme()

st.title("Product Intelligence")

st.caption(
    "Category, sub-category and product-level performance analysis"
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = load_processed_data()
filtered_df = sidebar_filters(df)

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()


# --------------------------------------------------
# PRODUCT-LEVEL AGGREGATION
# --------------------------------------------------

product_summary = (
    filtered_df
    .groupby(
        [
            "product_id",
            "product_name",
            "category",
            "sub_category"
        ],
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        quantity=("quantity", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        average_discount=("discount", "mean")
    )
)

product_summary["profit_margin_pct"] = np.where(
    product_summary["sales"] != 0,
    product_summary["profit"]
    / product_summary["sales"]
    * 100,
    0
)


# --------------------------------------------------
# CATEGORY SUMMARY
# --------------------------------------------------

category_summary = (
    filtered_df
    .groupby("category", as_index=False)
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        quantity=("quantity", "sum"),
        orders=("order_id", "nunique"),
        products=("product_id", "nunique"),
        average_discount=("discount", "mean")
    )
)

category_summary["profit_margin_pct"] = np.where(
    category_summary["sales"] != 0,
    category_summary["profit"]
    / category_summary["sales"]
    * 100,
    0
)


# --------------------------------------------------
# SUB-CATEGORY SUMMARY
# --------------------------------------------------

subcategory_summary = (
    filtered_df
    .groupby(
        ["category", "sub_category"],
        as_index=False
    )
    .agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        quantity=("quantity", "sum"),
        orders=("order_id", "nunique"),
        products=("product_id", "nunique"),
        average_discount=("discount", "mean")
    )
)

subcategory_summary["profit_margin_pct"] = np.where(
    subcategory_summary["sales"] != 0,
    subcategory_summary["profit"]
    / subcategory_summary["sales"]
    * 100,
    0
)


# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------

total_products = product_summary["product_id"].nunique()

profitable_products = len(
    product_summary[
        product_summary["profit"] > 0
    ]
)

loss_products = len(
    product_summary[
        product_summary["profit"] < 0
    ]
)

best_product = (
    product_summary
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)

top_sales_product = (
    product_summary
    .sort_values(
        "sales",
        ascending=False
    )
    .iloc[0]
)

worst_product = (
    product_summary
    .sort_values("profit")
    .iloc[0]
)

best_margin_product = (
    product_summary[
        product_summary["sales"] > 0
    ]
    .sort_values(
        "profit_margin_pct",
        ascending=False
    )
    .iloc[0]
)


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Products",
    f"{total_products:,}"
)

col2.metric(
    "Profitable Products",
    f"{profitable_products:,}"
)

col3.metric(
    "Loss-Making Products",
    f"{loss_products:,}"
)

col4.metric(
    "Product Profitability Rate",
    f"{profitable_products / total_products * 100:.1f}%"
)


col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "Highest Profit Product",
    f"${best_product['profit']:,.0f}"
)

col6.metric(
    "Highest Sales Product",
    f"${top_sales_product['sales']:,.0f}"
)

col7.metric(
    "Largest Product Loss",
    f"${worst_product['profit']:,.0f}"
)

col8.metric(
    "Best Product Margin",
    f"{best_margin_product['profit_margin_pct']:.1f}%"
)


st.divider()


# --------------------------------------------------
# INTERACTIVE PRODUCT DRILL-DOWN
# --------------------------------------------------

st.subheader("Product Drill-Down")


drill_col1, drill_col2 = st.columns(2)


with drill_col1:

    selected_category = st.selectbox(
        "Select Category",
        ["All"] +
        sorted(
            filtered_df["category"]
            .dropna()
            .unique()
            .tolist()
        )
    )


if selected_category == "All":

    available_subcategories = (
        filtered_df["sub_category"]
        .dropna()
        .unique()
        .tolist()
    )

else:

    available_subcategories = (
        filtered_df[
            filtered_df["category"]
            == selected_category
        ]["sub_category"]
        .dropna()
        .unique()
        .tolist()
    )


with drill_col2:

    selected_subcategory = st.selectbox(
        "Select Sub-Category",
        ["All"] +
        sorted(available_subcategories)
    )


drill_df = filtered_df.copy()

if selected_category != "All":
    drill_df = drill_df[
        drill_df["category"]
        == selected_category
    ]

if selected_subcategory != "All":
    drill_df = drill_df[
        drill_df["sub_category"]
        == selected_subcategory
    ]


st.info(
    f"Drill-down contains {len(drill_df):,} transaction records."
)


# --------------------------------------------------
# CATEGORY PERFORMANCE
# --------------------------------------------------

st.subheader("Category Performance")


left, right = st.columns(2)


with left:

    fig_category_sales = px.bar(
        category_summary.sort_values(
            "sales",
            ascending=False
        ),
        x="category",
        y="sales",
        text_auto=".2s",
        title="Category Sales"
    )

    st.plotly_chart(
        fig_category_sales,
        width="stretch"
    )


with right:

    fig_category_profit = px.bar(
        category_summary.sort_values(
            "profit",
            ascending=False
        ),
        x="category",
        y="profit",
        text_auto=".2s",
        title="Category Profit"
    )

    st.plotly_chart(
        fig_category_profit,
        width="stretch"
    )


# --------------------------------------------------
# SUB-CATEGORY PERFORMANCE
# --------------------------------------------------

st.subheader("Sub-Category Performance")


left, right = st.columns(2)


with left:

    fig_subcat_sales = px.bar(
        subcategory_summary.sort_values(
            "sales"
        ),
        x="sales",
        y="sub_category",
        orientation="h",
        color="category",
        title="Sales by Sub-Category"
    )

    st.plotly_chart(
        fig_subcat_sales,
        width="stretch"
    )


with right:

    fig_subcat_profit = px.bar(
        subcategory_summary.sort_values(
            "profit"
        ),
        x="profit",
        y="sub_category",
        orientation="h",
        color="category",
        title="Profit by Sub-Category"
    )

    st.plotly_chart(
        fig_subcat_profit,
        width="stretch"
    )


# --------------------------------------------------
# TOP AND BOTTOM PRODUCTS
# --------------------------------------------------

st.subheader("Product Ranking")


left, right = st.columns(2)


with left:

    top_products = (
        product_summary
        .nlargest(
            10,
            "profit"
        )
        .sort_values("profit")
    )

    fig_top_product = px.bar(
        top_products,
        x="profit",
        y="product_name",
        orientation="h",
        title="Top 10 Products by Profit"
    )

    st.plotly_chart(
        fig_top_product,
        width="stretch"
    )


with right:

    bottom_products = (
        product_summary
        .nsmallest(
            10,
            "profit"
        )
        .sort_values("profit")
    )

    fig_bottom_product = px.bar(
        bottom_products,
        x="profit",
        y="product_name",
        orientation="h",
        title="Bottom 10 Products by Profit"
    )

    st.plotly_chart(
        fig_bottom_product,
        width="stretch"
    )


# --------------------------------------------------
# TOP PRODUCTS BY SALES
# --------------------------------------------------

top_sales_products = (
    product_summary
    .nlargest(
        15,
        "sales"
    )
    .sort_values("sales")
)


fig_top_sales = px.bar(
    top_sales_products,
    x="sales",
    y="product_name",
    orientation="h",
    color="profit",
    title="Top 15 Products by Sales"
)

st.plotly_chart(
    fig_top_sales,
    width="stretch"
)


# --------------------------------------------------
# SALES VS PROFIT PRODUCT MATRIX
# --------------------------------------------------

st.subheader("Product Performance Matrix")


sales_median = product_summary["sales"].median()
profit_median = product_summary["profit"].median()


def classify_product(row):
    """Assign a product to a median-based sales and profit strategic group."""

    if (
        row["sales"] >= sales_median
        and row["profit"] >= profit_median
    ):
        return "Star"

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


product_summary["strategic_group"] = (
    product_summary.apply(
        classify_product,
        axis=1
    )
)


fig_matrix = px.scatter(
    product_summary,
    x="sales",
    y="profit",
    size="orders",
    color="strategic_group",
    hover_name="product_name",
    hover_data=[
        "category",
        "sub_category",
        "profit_margin_pct",
        "average_discount"
    ],
    title="Product Sales vs Profit Strategic Matrix"
)

fig_matrix.add_vline(
    x=sales_median,
    line_dash="dash"
)

fig_matrix.add_hline(
    y=profit_median,
    line_dash="dash"
)

st.plotly_chart(
    fig_matrix,
    width="stretch"
)


# --------------------------------------------------
# STRATEGIC GROUP COUNTS
# --------------------------------------------------

group_counts = (
    product_summary
    .groupby(
        "strategic_group",
        as_index=False
    )
    .agg(
        products=("product_id", "nunique"),
        sales=("sales", "sum"),
        profit=("profit", "sum")
    )
)


fig_groups = px.bar(
    group_counts,
    x="strategic_group",
    y="products",
    text_auto=True,
    title="Product Strategic Group Distribution"
)

st.plotly_chart(
    fig_groups,
    width="stretch"
)


# --------------------------------------------------
# PARETO / 80-20 ANALYSIS
# --------------------------------------------------

st.subheader("Pareto Profit Analysis")


positive_products = (
    product_summary[
        product_summary["profit"] > 0
    ]
    .sort_values(
        "profit",
        ascending=False
    )
    .copy()
)


if not positive_products.empty:

    positive_products["cumulative_profit"] = (
        positive_products["profit"]
        .cumsum()
    )

    total_positive_profit = (
        positive_products["profit"].sum()
    )

    positive_products["cumulative_profit_pct"] = (
        positive_products[
            "cumulative_profit"
        ]
        / total_positive_profit
        * 100
    )

    positive_products["product_rank"] = (
        np.arange(
            1,
            len(positive_products) + 1
        )
    )

    pareto_80 = positive_products[
        positive_products[
            "cumulative_profit_pct"
        ] <= 80
    ]

    if len(pareto_80) < len(
        positive_products
    ):
        pareto_count = (
            len(pareto_80) + 1
        )
    else:
        pareto_count = len(
            positive_products
        )

    pareto_share = (
        pareto_count
        / len(positive_products)
        * 100
    )


    fig_pareto = px.line(
        positive_products,
        x="product_rank",
        y="cumulative_profit_pct",
        title="Cumulative Contribution to Positive Profit"
    )

    fig_pareto.add_hline(
        y=80,
        line_dash="dash"
    )

    st.plotly_chart(
        fig_pareto,
        width="stretch"
    )


    st.info(
        f"""
        Approximately **{pareto_count} products**
        ({pareto_share:.1f}% of profitable products)
        are required to generate roughly
        **80% of positive product profit**.
        """
    )


# --------------------------------------------------
# DISCOUNT EXPOSURE
# --------------------------------------------------

st.subheader("Product Discount Exposure")


discount_product = (
    product_summary
    .sort_values(
        "average_discount",
        ascending=False
    )
    .head(20)
)


fig_discount = px.scatter(
    product_summary,
    x="average_discount",
    y="profit",
    size="sales",
    color="category",
    hover_name="product_name",
    title="Product Discount vs Profit"
)

fig_discount.update_layout(
    xaxis_title="Average Discount",
    yaxis_title="Profit ($)"
)

st.plotly_chart(
    fig_discount,
    width="stretch"
)


with st.expander(
    "View Highest Discount Products"
):

    st.dataframe(
        discount_product[
            [
                "product_name",
                "category",
                "sub_category",
                "sales",
                "profit",
                "average_discount",
                "profit_margin_pct"
            ]
        ],
        width="stretch"
    )


# --------------------------------------------------
# LOSS-MAKING PRODUCTS
# --------------------------------------------------

st.subheader("Loss-Making Product Analysis")


loss_product_df = (
    product_summary[
        product_summary["profit"] < 0
    ]
    .sort_values("profit")
)


if not loss_product_df.empty:

    st.error(
        f"{len(loss_product_df):,} products generate negative aggregate profit "
        "within the selected filters."
    )

    st.dataframe(
        loss_product_df[
            [
                "product_name",
                "category",
                "sub_category",
                "sales",
                "profit",
                "profit_margin_pct",
                "average_discount",
                "orders"
            ]
        ],
        width="stretch"
    )

else:

    st.success(
        "No products generate negative aggregate profit under the current filters."
    )


# --------------------------------------------------
# PRODUCT GROWTH OPPORTUNITIES
# --------------------------------------------------

st.subheader("Product Growth Opportunities")


growth_products = (
    product_summary[
        product_summary[
            "strategic_group"
        ]
        == "Growth Opportunity"
    ]
    .sort_values(
        "profit_margin_pct",
        ascending=False
    )
)


if not growth_products.empty:

    st.success(
        f"{len(growth_products)} products are classified as potential growth opportunities."
    )

    st.dataframe(
        growth_products[
            [
                "product_name",
                "category",
                "sub_category",
                "sales",
                "profit",
                "profit_margin_pct",
                "orders"
            ]
        ].head(20),
        width="stretch"
    )

else:

    st.info(
        "No products meet the current growth-opportunity classification."
    )


# --------------------------------------------------
# MARGIN RISK PRODUCTS
# --------------------------------------------------

st.subheader("Margin Risk Products")


margin_risk_products = (
    product_summary[
        product_summary[
            "strategic_group"
        ]
        == "Margin Risk"
    ]
    .sort_values(
        "sales",
        ascending=False
    )
)


if not margin_risk_products.empty:

    st.warning(
        f"{len(margin_risk_products)} products have relatively strong sales "
        "but weaker profitability."
    )

    st.dataframe(
        margin_risk_products[
            [
                "product_name",
                "category",
                "sub_category",
                "sales",
                "profit",
                "profit_margin_pct",
                "average_discount"
            ]
        ].head(20),
        width="stretch"
    )

else:

    st.success(
        "No clear margin-risk products were identified."
    )


# --------------------------------------------------
# DYNAMIC PRODUCT INSIGHTS
# --------------------------------------------------

st.divider()

st.subheader("Product Intelligence Insights")


best_category = (
    category_summary
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)


worst_category = (
    category_summary
    .sort_values("profit")
    .iloc[0]
)


best_subcategory = (
    subcategory_summary
    .sort_values(
        "profit",
        ascending=False
    )
    .iloc[0]
)


worst_subcategory = (
    subcategory_summary
    .sort_values("profit")
    .iloc[0]
)


insight1, insight2 = st.columns(2)


with insight1:

    st.success(
        f"""
        **Highest-Profit Product**

        {best_product['product_name']}

        Profit: ${best_product['profit']:,.0f}

        Sales: ${best_product['sales']:,.0f}

        Margin: {best_product['profit_margin_pct']:.1f}%
        """
    )

    st.success(
        f"""
        **Strongest Sub-Category**

        {best_subcategory['sub_category']}

        Profit: ${best_subcategory['profit']:,.0f}
        """
    )

    st.success(
        f"""
        **Strongest Category**

        {best_category['category']}

        Profit: ${best_category['profit']:,.0f}
        """
    )


with insight2:

    st.error(
        f"""
        **Largest Product Loss**

        {worst_product['product_name']}

        Profit: ${worst_product['profit']:,.0f}

        Sales: ${worst_product['sales']:,.0f}
        """
    )

    if worst_subcategory["profit"] < 0:

        st.error(
            f"""
            **Sub-Category Risk**

            {worst_subcategory['sub_category']}

            Profit: ${worst_subcategory['profit']:,.0f}
            """
        )

    else:

        st.warning(
            f"""
            **Lowest-Profit Sub-Category**

            {worst_subcategory['sub_category']}

            Profit: ${worst_subcategory['profit']:,.0f}
            """
        )

    st.warning(
        f"""
        **Lowest-Profit Category**

        {worst_category['category']}

        Profit: ${worst_category['profit']:,.0f}
        """
    )


# --------------------------------------------------
# MANAGEMENT RECOMMENDATIONS
# --------------------------------------------------

st.subheader("Product Management Recommendations")


st.success(
    f"""
    **Protect high-performing products:**  
    {best_product['product_name']} currently provides the strongest product-level
    profit contribution and should be monitored for stock availability,
    pricing consistency and continued customer demand.
    """
)


if loss_products > 0:

    st.error(
        f"""
        **Review loss-making products:**  
        {loss_products} products currently generate negative aggregate profit.
        Management should investigate pricing, discount intensity,
        product positioning and whether these products remain strategically justified.
        """
    )


if not margin_risk_products.empty:

    st.warning(
        """
        **Investigate margin-risk products:**  
        Some products generate strong sales but comparatively weak profit.
        These products should be reviewed before further promotional investment.
        """
    )


if not growth_products.empty:

    st.info(
        """
        **Explore growth opportunities:**  
        Products with lower sales but stronger profitability may justify
        additional marketing, visibility or distribution support.
        """
    )


if not positive_products.empty:

    st.info(
        f"""
        **Protect profit concentration:**  
        Roughly {pareto_count} products are needed to generate about 80%
        of positive product profit. Operational disruption affecting these
        products could have a disproportionate financial impact.
        """
    )


# --------------------------------------------------
# PRODUCT TABLE
# --------------------------------------------------

with st.expander(
    "View Complete Product Performance Table"
):

    st.dataframe(
        product_summary.sort_values(
            "profit",
            ascending=False
        ),
        width="stretch"
    )


# --------------------------------------------------
# DOWNLOAD DATA
# --------------------------------------------------

st.divider()

product_csv = (
    product_summary
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    label="Download Product Intelligence Data",
    data=product_csv,
    file_name="product_intelligence.csv",
    mime="text/csv"
)
