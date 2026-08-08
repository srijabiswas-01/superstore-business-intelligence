import streamlit as st

from utils.theme import apply_dashboard_theme
import pandas as pd
import numpy as np
import plotly.express as px

from utils.data_loader import (
    load_processed_data
)

from utils.ml_models import (
    train_profit_classifier,
    train_sales_regressor,
    load_profit_classifier,
    load_sales_regressor,
    predict_profitability,
    predict_sales
)


st.set_page_config(
    page_title="Predictive Analytics",
    layout="wide"
)

apply_dashboard_theme()

st.title("Predictive Analytics")

st.caption(
    "Machine-learning models for profitability risk and sales prediction"
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = load_processed_data()


# --------------------------------------------------
# MODEL STATUS
# --------------------------------------------------

classifier = load_profit_classifier()
regressor = load_sales_regressor()


st.subheader("Model Status")

status1, status2 = st.columns(2)


with status1:

    if classifier is None:

        st.warning(
            "Profitability classifier has not yet been trained."
        )

    else:

        st.success(
            "Profitability classifier is available."
        )


with status2:

    if regressor is None:

        st.warning(
            "Sales regression model has not yet been trained."
        )

    else:

        st.success(
            "Sales regression model is available."
        )


# --------------------------------------------------
# MODEL TRAINING
# --------------------------------------------------

st.subheader("Model Training and Evaluation")

st.caption(
    "Train or retrain models using the complete processed Superstore dataset."
)


if st.button(
    "Train / Retrain Models",
    type="primary"
):

    with st.spinner(
        "Training machine-learning models..."
    ):

        classifier, classifier_eval = (
            train_profit_classifier(df)
        )

        regressor, regressor_eval = (
            train_sales_regressor(df)
        )

    st.success(
        "Models trained and saved successfully."
    )

    st.session_state[
        "classifier_evaluation"
    ] = classifier_eval

    st.session_state[
        "regressor_evaluation"
    ] = regressor_eval


# --------------------------------------------------
# DISPLAY CLASSIFIER RESULTS
# --------------------------------------------------

if (
    "classifier_evaluation"
    in st.session_state
):

    classifier_eval = (
        st.session_state[
            "classifier_evaluation"
        ]
    )

    st.subheader(
        "Profitability Classification Results"
    )

    st.success(
        f"""
        Best Classification Model:
        **{classifier_eval['best_model_name']}**
        """
    )

    st.dataframe(
        classifier_eval["results"],
        width="stretch"
    )


    confusion = (
        classifier_eval[
            "confusion_matrix"
        ]
    )


    confusion_df = pd.DataFrame(
        confusion,
        index=[
            "Actual Loss",
            "Actual Profit"
        ],
        columns=[
            "Predicted Loss",
            "Predicted Profit"
        ]
    )


    fig_confusion = px.imshow(
        confusion_df,
        text_auto=True,
        title="Profitability Classification Confusion Matrix"
    )

    st.plotly_chart(
        fig_confusion,
        width="stretch"
    )


# --------------------------------------------------
# DISPLAY REGRESSION RESULTS
# --------------------------------------------------

if (
    "regressor_evaluation"
    in st.session_state
):

    regressor_eval = (
        st.session_state[
            "regressor_evaluation"
        ]
    )

    st.subheader(
        "Sales Regression Results"
    )

    st.success(
        f"""
        Best Regression Model:
        **{regressor_eval['best_model_name']}**
        """
    )

    st.dataframe(
        regressor_eval["results"],
        width="stretch"
    )


# --------------------------------------------------
# PREDICTION SIMULATOR
# --------------------------------------------------

st.divider()

st.subheader(
    "Interactive Prediction Simulator"
)

st.caption(
    "Enter transaction characteristics to estimate profitability risk and expected sales."
)


# --------------------------------------------------
# INPUT CONTROLS
# --------------------------------------------------

input_col1, input_col2 = st.columns(2)


with input_col1:

    quantity = st.number_input(
        "Quantity",
        min_value=1,
        max_value=int(
            df["quantity"].max()
        ),
        value=2,
        step=1
    )

    discount = st.slider(
        "Discount",
        min_value=0.0,
        max_value=float(
            df["discount"].max()
        ),
        value=0.10,
        step=0.01,
        format="%.2f"
    )

    shipping_delay = (
        st.number_input(
            "Shipping Delay (Days)",
            min_value=int(
                df["shipping_delay"].min()
            ),
            max_value=int(
                df["shipping_delay"].max()
            ),
            value=int(
                df["shipping_delay"].median()
            ),
            step=1
        )
    )

    ship_mode = st.selectbox(
        "Ship Mode",
        sorted(
            df["ship_mode"]
            .dropna()
            .unique()
        )
    )


with input_col2:

    segment = st.selectbox(
        "Customer Segment",
        sorted(
            df["segment"]
            .dropna()
            .unique()
        )
    )

    region = st.selectbox(
        "Region",
        sorted(
            df["region"]
            .dropna()
            .unique()
        )
    )

    category = st.selectbox(
        "Category",
        sorted(
            df["category"]
            .dropna()
            .unique()
        )
    )


    available_subcategories = (
        df[
            df["category"]
            == category
        ]["sub_category"]
        .dropna()
        .unique()
    )


    sub_category = st.selectbox(
        "Sub-Category",
        sorted(
            available_subcategories
        )
    )


# --------------------------------------------------
# INPUT DATAFRAME
# --------------------------------------------------

input_data = pd.DataFrame(
    [
        {
            "quantity": quantity,
            "discount": discount,
            "shipping_delay":
                shipping_delay,
            "ship_mode": ship_mode,
            "segment": segment,
            "region": region,
            "category": category,
            "sub_category":
                sub_category
        }
    ]
)


# --------------------------------------------------
# PREDICTION BUTTON
# --------------------------------------------------

if st.button(
    "Generate Prediction",
    type="primary",
    width="stretch"
):

    classifier = (
        load_profit_classifier()
    )

    regressor = (
        load_sales_regressor()
    )


    if (
        classifier is None
        or regressor is None
    ):

        st.error(
            "Train the models before generating predictions."
        )

    else:

        profitability = (
            predict_profitability(
                classifier,
                input_data
            )
        )

        sales_prediction = (
            predict_sales(
                regressor,
                input_data
            )
        )


        probability = (
            profitability[
                "profit_probability"
            ]
        )


        prediction = (
            profitability[
                "prediction"
            ]
        )


        # ------------------------------------------
        # RISK CLASSIFICATION
        # ------------------------------------------

        if probability is not None:

            if probability >= 0.70:

                risk = "Low Risk"

            elif probability >= 0.50:

                risk = "Moderate Risk"

            else:

                risk = "High Risk"

        else:

            risk = (
                "Profitability Risk"
                if prediction == 0
                else "Lower Risk"
            )


        # ------------------------------------------
        # RESULTS
        # ------------------------------------------

        result1, result2, result3 = (
            st.columns(3)
        )


        result1.metric(
            "Predicted Sales",
            f"${sales_prediction:,.2f}"
        )


        result2.metric(
            "Predicted Outcome",
            (
                "Profitable"
                if prediction == 1
                else "Loss-Making"
            )
        )


        if probability is not None:

            result3.metric(
                "Profit Probability",
                f"{probability:.1%}"
            )

        else:

            result3.metric(
                "Risk Classification",
                risk
            )


        # ------------------------------------------
        # RISK MESSAGE
        # ------------------------------------------

        if risk == "Low Risk":

            st.success(
                """
                **Low predicted profitability risk.**

                The model estimates a relatively high
                probability that the transaction will
                generate positive profit.
                """
            )

        elif risk == "Moderate Risk":

            st.warning(
                """
                **Moderate profitability risk.**

                Management may wish to review the
                transaction characteristics before
                applying additional discounting.
                """
            )

        else:

            st.error(
                """
                **High predicted profitability risk.**

                Review discount level, product category,
                customer segment and other transaction
                conditions before approval.
                """
            )


# --------------------------------------------------
# SCENARIO ANALYSIS
# --------------------------------------------------

st.divider()

st.subheader(
    "Discount What-If Analysis"
)

st.caption(
    "See how predicted profitability probability changes under alternative discount scenarios."
)


classifier = load_profit_classifier()


if classifier is not None:

    discount_levels = np.arange(
        0,
        min(
            float(
                df["discount"].max()
            ),
            0.80
        ) + 0.01,
        0.05
    )


    scenario_results = []


    for scenario_discount in (
        discount_levels
    ):

        scenario_input = (
            input_data.copy()
        )

        scenario_input[
            "discount"
        ] = scenario_discount


        prediction_result = (
            predict_profitability(
                classifier,
                scenario_input
            )
        )


        scenario_results.append(
            {
                "discount":
                    scenario_discount,

                "profit_probability":
                    prediction_result[
                        "profit_probability"
                    ]
            }
        )


    scenario_df = pd.DataFrame(
        scenario_results
    )


    if (
        scenario_df[
            "profit_probability"
        ].notna().any()
    ):

        scenario_df[
            "discount_pct"
        ] = (
            scenario_df["discount"]
            * 100
        )


        scenario_df[
            "profit_probability_pct"
        ] = (
            scenario_df[
                "profit_probability"
            ]
            * 100
        )


        fig_scenario = px.line(
            scenario_df,
            x="discount_pct",
            y="profit_probability_pct",
            markers=True,
            title=(
                "Predicted Profitability "
                "Probability by Discount Level"
            )
        )


        fig_scenario.update_layout(
            xaxis_title="Discount (%)",
            yaxis_title=(
                "Predicted Profit "
                "Probability (%)"
            )
        )


        st.plotly_chart(
            fig_scenario,
            width="stretch"
        )


else:

    st.info(
        "Train the profitability model to enable what-if analysis."
    )


# --------------------------------------------------
# BUSINESS INTERPRETATION
# --------------------------------------------------

st.divider()

st.subheader(
    "Predictive Analytics Interpretation"
)


st.info(
    """
    **Profitability Classification**

    The classification model estimates whether
    a transaction is likely to produce positive
    or negative profit based on quantity,
    discount, shipping delay, ship mode,
    customer segment, region, category and
    sub-category.
    """
)


st.info(
    """
    **Sales Regression**

    The regression model estimates expected
    transaction sales from the available
    transaction characteristics.

    The model should be interpreted using
    MAE, RMSE and R² rather than relying
    only on the predicted value.
    """
)


# --------------------------------------------------
# MODEL LIMITATIONS
# --------------------------------------------------

st.warning(
    """
    **Important Model Limitations**

    These predictions identify statistical patterns
    in the historical Sample Superstore dataset.

    They do not prove causal relationships and
    should not replace commercial judgement.

    The dataset does not include product cost,
    inventory availability, competitor pricing,
    marketing expenditure, customer satisfaction,
    economic conditions or actual freight cost.
    These missing variables limit predictive accuracy.
    """
)