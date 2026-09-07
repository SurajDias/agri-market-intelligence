import pandas as pd
import numpy as np

INPUT_FILE = "data/processed/mandi_prices_clean.csv"


def naive_baseline(df):
    """
    Naive baseline:
    Predict tomorrow's price using today's modal price.
    """

    df = df.sort_values(["market", "arrival_date"]).copy()

    # Previous day's modal price becomes the prediction
    df["predicted_price"] = (
        df.groupby("market")["modal_price"].shift(1)
    )

    # Remove rows where prediction is not available
    df = df.dropna(subset=["predicted_price"])

    return df


def calculate_metrics(df):
    """Calculate MAPE and RMSE."""

    actual = df["modal_price"]
    predicted = df["predicted_price"]

    mape = (
        np.mean(np.abs((actual - predicted) / actual)) * 100
    )

    rmse = np.sqrt(
        np.mean((actual - predicted) ** 2)
    )

    return mape, rmse


if __name__ == "__main__":

    print("Loading cleaned data...")

    df = pd.read_csv(INPUT_FILE)

    df["arrival_date"] = pd.to_datetime(df["arrival_date"])

    print("Records:", len(df))

    baseline_df = naive_baseline(df)

    mape, rmse = calculate_metrics(baseline_df)

    print("\n===== NAIVE BASELINE RESULTS =====")
    print(f"MAPE: {mape:.2f}%")
    print(f"RMSE: {rmse:.2f}")

    print("\nSample predictions:")
    print(
        baseline_df[
            ["market", "arrival_date", "modal_price", "predicted_price"]
        ].head(10)
    )