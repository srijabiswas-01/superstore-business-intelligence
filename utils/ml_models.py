from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

CLASSIFIER_PATH = MODEL_DIR / "profit_classifier.pkl"
REGRESSOR_PATH = MODEL_DIR / "sales_regressor.pkl"


NUMERIC_FEATURES = [
    "quantity",
    "discount",
    "shipping_delay"
]

CATEGORICAL_FEATURES = [
    "ship_mode",
    "segment",
    "region",
    "category",
    "sub_category"
]

MODEL_FEATURES = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)


def build_preprocessor():
    """Build preprocessing shared by classification and regression pipelines.

    Numeric fields receive median imputation and standardization; categorical
    fields receive most-frequent imputation and one-hot encoding that tolerates
    unseen values. Returns a scikit-learn ``ColumnTransformer``.
    """

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                )
            ),
            (
                "scaler",
                StandardScaler()
            )
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                )
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore"
                )
            )
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES
            )
        ]
    )

    return preprocessor


def train_profit_classifier(df):
    """Train, compare, select, and persist transaction-profit classifiers.

    The function creates a stratified train/test split, evaluates Logistic
    Regression and Random Forest pipelines, selects the strongest candidate,
    saves it to disk, and returns the model plus comparison/evaluation details.

    Args:
        df: Feature-engineered transactions containing ``profit_flag``.
    """

    data = df.dropna(
        subset=["profit_flag"]
    ).copy()

    X = data[MODEL_FEATURES]
    y = data["profit_flag"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    models = {
        "Logistic Regression":
            LogisticRegression(
                max_iter=3000,
                class_weight="balanced"
            ),

        "Random Forest":
            RandomForestClassifier(
                n_estimators=300,
                random_state=42,
                class_weight="balanced",
                n_jobs=-1
            )
    }

    results = []
    fitted_models = {}

    for name, model in models.items():

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    build_preprocessor()
                ),
                (
                    "model",
                    model
                )
            ]
        )

        pipeline.fit(
            X_train,
            y_train
        )

        predictions = pipeline.predict(
            X_test
        )

        results.append(
            {
                "Model": name,
                "Accuracy": accuracy_score(
                    y_test,
                    predictions
                ),
                "Precision": precision_score(
                    y_test,
                    predictions,
                    zero_division=0
                ),
                "Recall": recall_score(
                    y_test,
                    predictions,
                    zero_division=0
                ),
                "F1": f1_score(
                    y_test,
                    predictions,
                    zero_division=0
                )
            }
        )

        fitted_models[name] = pipeline

    results_df = (
        pd.DataFrame(results)
        .sort_values(
            "F1",
            ascending=False
        )
    )

    best_model_name = (
        results_df.iloc[0]["Model"]
    )

    best_model = (
        fitted_models[
            best_model_name
        ]
    )

    best_predictions = (
        best_model.predict(
            X_test
        )
    )

    evaluation = {
        "results": results_df,
        "best_model_name":
            best_model_name,
        "confusion_matrix":
            confusion_matrix(
                y_test,
                best_predictions
            ),
        "classification_report":
            classification_report(
                y_test,
                best_predictions,
                output_dict=True,
                zero_division=0
            )
    }

    joblib.dump(
        best_model,
        CLASSIFIER_PATH
    )

    return best_model, evaluation


def train_sales_regressor(df):
    """Train, compare, select, and persist transaction-sales regressors.

    Linear Regression and Random Forest pipelines are evaluated on a fixed
    holdout split. The selected model is saved and returned with performance
    metrics and prediction results for dashboard presentation.

    Args:
        df: Feature-engineered transactions containing the sales target.
    """

    data = df.dropna(
        subset=["sales"]
    ).copy()

    X = data[MODEL_FEATURES]
    y = data["sales"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42
    )

    models = {
        "Linear Regression":
            LinearRegression(),

        "Random Forest":
            RandomForestRegressor(
                n_estimators=300,
                random_state=42,
                n_jobs=-1
            )
    }

    results = []
    fitted_models = {}

    for name, model in models.items():

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    build_preprocessor()
                ),
                (
                    "model",
                    model
                )
            ]
        )

        pipeline.fit(
            X_train,
            y_train
        )

        predictions = pipeline.predict(
            X_test
        )

        mae = mean_absolute_error(
            y_test,
            predictions
        )

        rmse = np.sqrt(
            mean_squared_error(
                y_test,
                predictions
            )
        )

        r2 = r2_score(
            y_test,
            predictions
        )

        results.append(
            {
                "Model": name,
                "MAE": mae,
                "RMSE": rmse,
                "R2": r2
            }
        )

        fitted_models[name] = pipeline

    results_df = (
        pd.DataFrame(results)
        .sort_values(
            "R2",
            ascending=False
        )
    )

    best_model_name = (
        results_df.iloc[0]["Model"]
    )

    best_model = (
        fitted_models[
            best_model_name
        ]
    )

    evaluation = {
        "results": results_df,
        "best_model_name":
            best_model_name
    }

    joblib.dump(
        best_model,
        REGRESSOR_PATH
    )

    return best_model, evaluation


def load_profit_classifier():
    """Load the persisted profit classifier, or return ``None`` if unavailable."""

    if CLASSIFIER_PATH.exists():

        return joblib.load(
            CLASSIFIER_PATH
        )

    return None


def load_sales_regressor():
    """Load the persisted sales regressor, or return ``None`` if unavailable."""

    if REGRESSOR_PATH.exists():

        return joblib.load(
            REGRESSOR_PATH
        )

    return None


def predict_profitability(
    model,
    input_data
):
    """Predict whether input transactions will be profitable.

    Returns the first binary prediction and, when supported by the estimator,
    its positive-class probability. ``input_data`` must contain model features
    in the schema expected by the fitted preprocessing pipeline.
    """

    prediction = (
        model.predict(
            input_data
        )[0]
    )

    probability = None

    if hasattr(
        model,
        "predict_proba"
    ):

        probability = (
            model.predict_proba(
                input_data
            )[0][1]
        )

    return {
        "prediction":
            int(prediction),

        "profit_probability":
            probability
    }


def predict_sales(
    model,
    input_data
):
    """Predict sales for the first input row and clamp negative estimates to zero."""

    prediction = (
        model.predict(
            input_data
        )[0]
    )

    return max(
        float(prediction),
        0
    )
