import pandas as pd


def clean_data(df):
    """Standardize and validate raw Superstore transactions.

    Args:
        df: Raw transaction DataFrame loaded from the source CSV.

    Returns:
        A copy with normalized column names, parsed dates, numeric measures,
        duplicate rows removed, and incomplete core transactions excluded.
    """
    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    df["order_date"] = pd.to_datetime(
        df["order_date"],
        errors="coerce"
    )

    df["ship_date"] = pd.to_datetime(
        df["ship_date"],
        errors="coerce"
    )

    for col in ["sales", "profit", "quantity", "discount"]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.drop_duplicates()

    df = df.dropna(
        subset=[
            "order_date",
            "ship_date",
            "sales",
            "profit"
        ]
    )

    return df
