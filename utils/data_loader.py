from pathlib import Path
import pandas as pd
import streamlit as st

from utils.data_cleaning import clean_data
from utils.feature_engineering import create_features


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "Sample_Superstore.csv"


@st.cache_data
def load_raw_data():
    """Load and cache the source Superstore CSV.

    Returns:
        The unmodified source data as a DataFrame.

    Raises:
        FileNotFoundError: If the configured dataset is unavailable.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Sample_Superstore.csv not found inside the data folder."
        )

    df = pd.read_csv(
        DATA_PATH,
        encoding="latin1"
    )

    return df


@st.cache_data
def load_processed_data():
    """Load, clean, engineer, and cache analysis-ready transactions.

    Returns:
        A DataFrame containing standardized source fields and all derived
        analytical features used throughout the dashboards.
    """
    df = load_raw_data()
    df = clean_data(df)
    df = create_features(df)

    return df
