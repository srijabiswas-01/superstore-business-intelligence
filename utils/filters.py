import streamlit as st


def reset_filters():
    """Clear all shared dashboard filter values from Streamlit session state."""
    st.session_state["year_filter"] = []
    st.session_state["region_filter"] = []
    st.session_state["category_filter"] = []
    st.session_state["segment_filter"] = []


def sidebar_filters(df):
    """Render shared sidebar controls and apply them to a transaction table.

    Args:
        df: Processed Superstore transactions available to the current page.

    Returns:
        A filtered DataFrame matching the selected years, regions, categories,
        and customer segments; empty selections mean no restriction.
    """
    st.sidebar.header("Dashboard Filters")

    st.sidebar.button(
        "Reset Filters",
        on_click=reset_filters,
        width="stretch"
    )

    years = st.sidebar.multiselect(
        "Year",
        sorted(df["order_year"].dropna().unique()),
        key="year_filter"
    )

    regions = st.sidebar.multiselect(
        "Region",
        sorted(df["region"].dropna().unique()),
        key="region_filter"
    )

    categories = st.sidebar.multiselect(
        "Category",
        sorted(df["category"].dropna().unique()),
        key="category_filter"
    )

    segments = st.sidebar.multiselect(
        "Segment",
        sorted(df["segment"].dropna().unique()),
        key="segment_filter"
    )

    filtered_df = df.copy()

    if years:
        filtered_df = filtered_df[
            filtered_df["order_year"].isin(years)
        ]

    if regions:
        filtered_df = filtered_df[
            filtered_df["region"].isin(regions)
        ]

    if categories:
        filtered_df = filtered_df[
            filtered_df["category"].isin(categories)
        ]

    if segments:
        filtered_df = filtered_df[
            filtered_df["segment"].isin(segments)
        ]

    return filtered_df
