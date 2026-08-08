from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error
)


# --------------------------------------------------
# MODEL PATH
# --------------------------------------------------

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

FORECAST_MODEL_PATH = (
    MODEL_DIR / "forecasting_model.pkl"
)


# --------------------------------------------------
# PREPARE MONTHLY SALES
# --------------------------------------------------

def prepare_monthly_sales(df):
    """Convert transaction sales into a continuous month-start time series.

    Missing months are filled with zero sales and invalid date/sales rows are
    excluded. An empty input produces an empty floating-point Series.
    """

    if df.empty:
        return pd.Series(dtype=float)

    data = df.copy()

    data = data.dropna(
        subset=[
            "order_date",
            "sales"
        ]
    )

    monthly_sales = (
        data
        .set_index("order_date")
        .resample("MS")["sales"]
        .sum()
        .asfreq("MS", fill_value=0)
    )

    monthly_sales = monthly_sales.astype(
        float
    )

    return monthly_sales


# --------------------------------------------------
# TRAIN / TEST SPLIT
# --------------------------------------------------

def split_time_series(
    series,
    test_months=None
):
    """Split chronological observations into training and holdout periods.

    Uses the requested holdout length or 20 percent with a six-month minimum,
    while retaining at least six training observations. At least 12 monthly
    observations are required. Returns ``(train, test)`` Series objects.
    """

    if len(series) < 12:
        raise ValueError(
            "At least 12 months of historical "
            "data are required for forecasting."
        )

    if test_months is None:

        test_months = max(
            6,
            int(len(series) * 0.20)
        )

    test_months = min(
        test_months,
        len(series) - 6
    )

    train = series.iloc[
        :-test_months
    ]

    test = series.iloc[
        -test_months:
    ]

    return train, test


# --------------------------------------------------
# TRAIN ARIMA
# --------------------------------------------------

def train_arima(
    train_series,
    order=(1, 1, 1)
):
    """Fit an ARIMA model to a training series.

    Args:
        train_series: Chronologically ordered numeric observations.
        order: ARIMA autoregressive, differencing, and moving-average orders.

    Returns:
        A fitted statsmodels ARIMA results object.
    """

    model = ARIMA(
        train_series,
        order=order
    )

    fitted_model = model.fit()

    return fitted_model


# --------------------------------------------------
# EVALUATE FORECAST
# --------------------------------------------------

def evaluate_forecast(
    test_series,
    predictions
):
    """Measure forecast accuracy against a holdout series.

    Aligns predictions to the test index and returns MAE, RMSE, MAPE, R-squared,
    and the aligned prediction Series. Zero actuals are excluded from MAPE.
    """

    predictions = pd.Series(
        predictions,
        index=test_series.index
    )

    mae = mean_absolute_error(
        test_series,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            test_series,
            predictions
        )
    )

    mape_mask = (
        test_series != 0
    )

    if mape_mask.any():

        mape = (
            np.mean(
                np.abs(
                    (
                        test_series[
                            mape_mask
                        ]
                        -
                        predictions[
                            mape_mask
                        ]
                    )
                    /
                    test_series[
                        mape_mask
                    ]
                )
            )
            * 100
        )

    else:
        mape = np.nan

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE": mape
    }


# --------------------------------------------------
# BACKTEST ARIMA
# --------------------------------------------------

def backtest_arima(
    series,
    order=(1, 1, 1),
    test_months=None
):
    """Train and evaluate ARIMA using the final months as unseen history.

    Returns the fitted training model, train/test Series, aligned predictions,
    and evaluation metrics so the forecasting page can visualize the backtest.
    """

    train, test = split_time_series(
        series,
        test_months=test_months
    )

    model = train_arima(
        train,
        order=order
    )

    predictions = model.forecast(
        steps=len(test)
    )

    predictions.index = (
        test.index
    )

    metrics = evaluate_forecast(
        test,
        predictions
    )

    result = pd.DataFrame(
        {
            "actual": test,
            "forecast": predictions
        }
    )

    return {
        "train": train,
        "test": test,
        "predictions": predictions,
        "metrics": metrics,
        "result": result,
        "model": model
    }


# --------------------------------------------------
# TRAIN FINAL MODEL
# --------------------------------------------------

def train_final_forecast_model(
    series,
    order=(1, 1, 1)
):
    """Fit ARIMA on all available history and persist the fitted model.

    The saved Joblib artifact is used for later future forecasts. The fitted
    statsmodels results object is also returned to the caller.
    """

    model = ARIMA(
        series,
        order=order
    )

    fitted_model = model.fit()

    joblib.dump(
        fitted_model,
        FORECAST_MODEL_PATH
    )

    return fitted_model


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

def load_forecast_model():
    """Load the persisted ARIMA model, or return ``None`` when it does not exist."""

    if FORECAST_MODEL_PATH.exists():

        return joblib.load(
            FORECAST_MODEL_PATH
        )

    return None


# --------------------------------------------------
# FUTURE FORECAST
# --------------------------------------------------

def forecast_future(
    model,
    last_date,
    periods=6
):
    """Generate future monthly forecasts with 95 percent confidence intervals.

    Args:
        model: Fitted statsmodels forecast model.
        last_date: Final observed month used to start the future date index.
        periods: Number of future months to predict.

    Returns:
        A DataFrame containing future dates, point forecasts, and lower/upper
        confidence bounds, with negative monetary forecasts clipped to zero.
    """

    forecast_result = (
        model.get_forecast(
            steps=periods
        )
    )

    predicted_mean = (
        forecast_result.predicted_mean
    )

    confidence_interval = (
        forecast_result.conf_int(
            alpha=0.05
        )
    )

    future_dates = pd.date_range(
        start=(
            pd.Timestamp(last_date)
            + pd.offsets.MonthBegin(1)
        ),
        periods=periods,
        freq="MS"
    )

    forecast_df = pd.DataFrame(
        {
            "date": future_dates,
            "forecast_sales":
                np.maximum(
                    predicted_mean.values,
                    0
                ),
            "lower_ci":
                np.maximum(
                    confidence_interval.iloc[
                        :, 0
                    ].values,
                    0
                ),
            "upper_ci":
                np.maximum(
                    confidence_interval.iloc[
                        :, 1
                    ].values,
                    0
                )
        }
    )

    return forecast_df
