import streamlit as st

from utils.theme import apply_dashboard_theme
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import (
    load_processed_data
)

from utils.filters import (
    sidebar_filters
)

from utils.forecasting import (
    prepare_monthly_sales,
    backtest_arima,
    train_final_forecast_model,
    load_forecast_model,
    forecast_future
)


st.set_page_config(
    page_title="Sales Forecasting",
    layout="wide"
)

apply_dashboard_theme()

st.title("Sales Forecasting")

st.caption(
    "Time-series forecasting for future "
    "Superstore sales planning"
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = load_processed_data()

filtered_df = sidebar_filters(df)


if filtered_df.empty:

    st.warning(
        "No records match the selected filters."
    )

    st.stop()


# --------------------------------------------------
# PREPARE MONTHLY SALES
# --------------------------------------------------

monthly_sales = prepare_monthly_sales(
    filtered_df
)


if len(monthly_sales) < 12:

    st.error(
        """
        Forecasting requires at least 12 months
        of historical sales data.

        Broaden the current filters and try again.
        """
    )

    st.stop()


# --------------------------------------------------
# BASIC FORECASTING KPIs
# --------------------------------------------------

historical_months = len(
    monthly_sales
)

average_monthly_sales = (
    monthly_sales.mean()
)

highest_month = (
    monthly_sales.idxmax()
)

highest_month_sales = (
    monthly_sales.max()
)

lowest_month = (
    monthly_sales.idxmin()
)

lowest_month_sales = (
    monthly_sales.min()
)


col1, col2, col3, col4 = (
    st.columns(4)
)


col1.metric(
    "Historical Months",
    f"{historical_months}"
)


col2.metric(
    "Average Monthly Sales",
    f"${average_monthly_sales:,.0f}"
)


col3.metric(
    "Highest Sales Month",
    highest_month.strftime(
        "%b %Y"
    ),
    f"${highest_month_sales:,.0f}"
)


col4.metric(
    "Lowest Sales Month",
    lowest_month.strftime(
        "%b %Y"
    ),
    f"${lowest_month_sales:,.0f}"
)


st.divider()


# --------------------------------------------------
# HISTORICAL SALES
# --------------------------------------------------

historical_df = (
    monthly_sales
    .reset_index()
)

historical_df.columns = [
    "date",
    "sales"
]


fig_history = px.line(
    historical_df,
    x="date",
    y="sales",
    markers=True,
    title="Historical Monthly Sales"
)


fig_history.update_layout(
    xaxis_title="Month",
    yaxis_title="Sales ($)"
)


st.plotly_chart(
    fig_history,
    width="stretch"
)


# --------------------------------------------------
# MODEL SETTINGS
# --------------------------------------------------

st.subheader(
    " Forecast Model Configuration"
)


setting1, setting2 = (
    st.columns(2)
)


with setting1:

    test_months = st.slider(
        "Backtest Months",
        min_value=3,
        max_value=min(
            12,
            len(monthly_sales) - 6
        ),
        value=min(
            9,
            len(monthly_sales) - 6
        )
    )


with setting2:

    forecast_horizon = st.slider(
        "Future Forecast Horizon",
        min_value=3,
        max_value=24,
        value=6
    )


st.caption(
    """
    The backtest holds out the most recent
    historical months and evaluates how accurately
    ARIMA forecasts periods it has not been trained on.
    """
)


# --------------------------------------------------
# BACKTEST MODEL
# --------------------------------------------------

st.subheader(
    "Forecast Model Evaluation"
)


try:

    backtest_result = (
        backtest_arima(
            monthly_sales,
            order=(1, 1, 1),
            test_months=test_months
        )
    )


    metrics = (
        backtest_result[
            "metrics"
        ]
    )


    metric1, metric2, metric3 = (
        st.columns(3)
    )


    metric1.metric(
        "MAE",
        f"${metrics['MAE']:,.0f}"
    )


    metric2.metric(
        "RMSE",
        f"${metrics['RMSE']:,.0f}"
    )


    if not np.isnan(
        metrics["MAPE"]
    ):

        metric3.metric(
            "MAPE",
            f"{metrics['MAPE']:.1f}%"
        )

    else:

        metric3.metric(
            "MAPE",
            "N/A"
        )


    # --------------------------------------------------
    # BACKTEST VISUAL
    # --------------------------------------------------

    train_df = (
        backtest_result[
            "train"
        ]
        .reset_index()
    )

    train_df.columns = [
        "date",
        "sales"
    ]

    train_df["series"] = (
        "Training"
    )


    test_df = (
        backtest_result[
            "test"
        ]
        .reset_index()
    )

    test_df.columns = [
        "date",
        "sales"
    ]

    test_df["series"] = (
        "Actual"
    )


    forecast_test_df = (
        backtest_result[
            "predictions"
        ]
        .reset_index()
    )

    forecast_test_df.columns = [
        "date",
        "sales"
    ]

    forecast_test_df["series"] = (
        "Forecast"
    )


    comparison_df = pd.concat(
        [
            train_df,
            test_df,
            forecast_test_df
        ],
        ignore_index=True
    )


    fig_backtest = px.line(
        comparison_df,
        x="date",
        y="sales",
        color="series",
        markers=True,
        title=(
            "ARIMA Backtest: "
            "Forecast vs Actual"
        )
    )


    fig_backtest.update_layout(
        xaxis_title="Month",
        yaxis_title="Sales ($)"
    )


    st.plotly_chart(
        fig_backtest,
        width="stretch"
    )


except Exception as e:

    st.error(
        f"Forecast evaluation failed: {e}"
    )

    st.stop()


# --------------------------------------------------
# ACTUAL VS FORECAST TABLE
# --------------------------------------------------

with st.expander(
    "View Backtest Forecast Data"
):

    backtest_table = (
        backtest_result[
            "result"
        ]
        .reset_index()
    )

    backtest_table.columns = [
        "date",
        "actual_sales",
        "forecast_sales"
    ]

    backtest_table[
        "absolute_error"
    ] = abs(
        backtest_table[
            "actual_sales"
        ]
        -
        backtest_table[
            "forecast_sales"
        ]
    )

    st.dataframe(
        backtest_table,
        width="stretch"
    )


# --------------------------------------------------
# TRAIN FINAL MODEL
# --------------------------------------------------

st.divider()

st.subheader(
    "Future Sales Forecast"
)


if st.button(
    "Train Final Forecast Model",
    type="primary",
    width="stretch"
):

    try:

        with st.spinner(
            "Training ARIMA model..."
        ):

            final_model = (
                train_final_forecast_model(
                    monthly_sales,
                    order=(1, 1, 1)
                )
            )

        st.success(
            """
            Forecast model trained successfully
            and saved to models/forecasting_model.pkl.
            """
        )

    except Exception as e:

        st.error(
            f"Model training failed: {e}"
        )


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

forecast_model = (
    load_forecast_model()
)


if forecast_model is None:

    st.info(
        """
        Train the final forecasting model
        before generating future forecasts.
        """
    )


else:

    try:

        forecast_df = forecast_future(
            forecast_model,
            last_date=monthly_sales.index.max(),
            periods=forecast_horizon
        )


        # --------------------------------------------------
        # FORECAST KPI
        # --------------------------------------------------

        forecast_total = (
            forecast_df[
                "forecast_sales"
            ].sum()
        )

        forecast_average = (
            forecast_df[
                "forecast_sales"
            ].mean()
        )

        strongest_future_month = (
            forecast_df.loc[
                forecast_df[
                    "forecast_sales"
                ].idxmax()
            ]
        )


        f1, f2, f3 = (
            st.columns(3)
        )


        f1.metric(
            f"Forecast Sales – Next {forecast_horizon} Months",
            f"${forecast_total:,.0f}"
        )


        f2.metric(
            "Average Forecast Monthly Sales",
            f"${forecast_average:,.0f}"
        )


        f3.metric(
            "Highest Forecast Month",
            strongest_future_month[
                "date"
            ].strftime(
                "%b %Y"
            ),
            f"${strongest_future_month['forecast_sales']:,.0f}"
        )


        # --------------------------------------------------
        # COMBINED FORECAST VISUAL
        # --------------------------------------------------

        fig_forecast = (
            go.Figure()
        )


        fig_forecast.add_trace(
            go.Scatter(
                x=historical_df[
                    "date"
                ],
                y=historical_df[
                    "sales"
                ],
                mode="lines+markers",
                name="Historical Sales"
            )
        )


        fig_forecast.add_trace(
            go.Scatter(
                x=forecast_df[
                    "date"
                ],
                y=forecast_df[
                    "forecast_sales"
                ],
                mode="lines+markers",
                name="Forecast"
            )
        )


        # Upper confidence interval
        fig_forecast.add_trace(
            go.Scatter(
                x=forecast_df[
                    "date"
                ],
                y=forecast_df[
                    "upper_ci"
                ],
                mode="lines",
                line=dict(
                    width=0
                ),
                showlegend=False,
                hoverinfo="skip"
            )
        )


        # Lower confidence interval
        fig_forecast.add_trace(
            go.Scatter(
                x=forecast_df[
                    "date"
                ],
                y=forecast_df[
                    "lower_ci"
                ],
                mode="lines",
                line=dict(
                    width=0
                ),
                fill="tonexty",
                name="95% Confidence Interval"
            )
        )


        fig_forecast.update_layout(
            title=(
                f"{forecast_horizon}-Month "
                "Sales Forecast"
            ),
            xaxis_title="Month",
            yaxis_title="Sales ($)"
        )


        st.plotly_chart(
            fig_forecast,
            width="stretch"
        )


        # --------------------------------------------------
        # FORECAST TABLE
        # --------------------------------------------------

        st.subheader(
            "Future Forecast Data"
        )


        display_forecast = (
            forecast_df.copy()
        )


        display_forecast[
            "date"
        ] = display_forecast[
            "date"
        ].dt.strftime(
            "%b %Y"
        )


        for col in [
            "forecast_sales",
            "lower_ci",
            "upper_ci"
        ]:

            display_forecast[
                col
            ] = display_forecast[
                col
            ].round(2)


        st.dataframe(
            display_forecast,
            width="stretch"
        )


        # --------------------------------------------------
        # DYNAMIC FORECAST INSIGHTS
        # --------------------------------------------------

        st.divider()

        st.subheader(
            "Forecasting Insights"
        )


        last_actual_sales = (
            monthly_sales.iloc[-1]
        )


        first_forecast_sales = (
            forecast_df[
                "forecast_sales"
            ].iloc[0]
        )


        initial_change = (
            (
                first_forecast_sales
                -
                last_actual_sales
            )
            /
            last_actual_sales
            * 100
            if last_actual_sales != 0
            else 0
        )


        if initial_change > 0:

            st.success(
                f"""
                **Near-Term Direction**

                The first forecast month is approximately
                **{initial_change:.1f}% above**
                the latest historical month's sales.
                """
            )

        elif initial_change < 0:

            st.warning(
                f"""
                **Near-Term Direction**

                The first forecast month is approximately
                **{abs(initial_change):.1f}% below**
                the latest historical month's sales.
                """
            )

        else:

            st.info(
                """
                The first forecast month is broadly
                consistent with the latest observed sales.
                """
            )


        st.info(
            f"""
            The model forecasts approximately
            **${forecast_total:,.0f}**
            in cumulative sales over the next
            **{forecast_horizon} months**.
            """
        )


        st.success(
            f"""
            The strongest forecast month is
            **{strongest_future_month['date'].strftime('%B %Y')}**
            with expected sales of approximately
            **${strongest_future_month['forecast_sales']:,.0f}**.
            """
        )


        # --------------------------------------------------
        # DOWNLOAD
        # --------------------------------------------------

        forecast_csv = (
            forecast_df
            .to_csv(
                index=False
            )
            .encode(
                "utf-8"
            )
        )


        st.download_button(
            label="Download Forecast Data",
            data=forecast_csv,
            file_name=(
                "future_sales_forecast.csv"
            ),
            mime="text/csv"
        )


    except Exception as e:

        st.error(
            f"Future forecasting failed: {e}"
        )


# --------------------------------------------------
# BUSINESS INTERPRETATION
# --------------------------------------------------

st.divider()

st.subheader(
    "Forecast Management Interpretation"
)


st.info(
    """
    Sales forecasts can support budgeting,
    inventory preparation, staffing and
    promotional planning.

    Forecasts should be treated as estimates,
    particularly when the confidence interval
    becomes wider over longer horizons.
    """
)


st.warning(
    """
    **Forecasting limitation**

    The Sample Superstore dataset contains only
    historical transaction information.

    It does not contain external variables such as
    inflation, economic growth, competitor activity,
    marketing campaigns, stock availability or
    future pricing changes.

    The forecast therefore represents a statistical
    continuation of historical sales patterns rather
    than a guaranteed future outcome.
    """
)