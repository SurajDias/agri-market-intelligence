import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error

INPUT_FILE = "data/processed/mandi_prices_clean.csv"


def prepare_data(df):
    df["arrival_date"] = pd.to_datetime(df["arrival_date"])

    df = df.sort_values(["market", "arrival_date"]).copy()

    # Previous prices
    df["lag_1"] = df.groupby("market")["modal_price"].shift(1)
    df["lag_2"] = df.groupby("market")["modal_price"].shift(2)

    # Previous day's arrivals
    df["arrival_lag_1"] = df.groupby("market")["arrivals"].shift(1)

    # Remove rows without enough history
    df = df.dropna(
        subset=["lag_1", "lag_2", "arrival_lag_1"]
    )

    return df


def evaluate_model():

    print("Loading data...")

    df = pd.read_csv(INPUT_FILE)

    df = prepare_data(df)

    # Sort by date for time-based evaluation
    df = df.sort_values("arrival_date")

    features = [
        "lag_1",
        "lag_2",
        "arrival_lag_1"
    ]

    X = df[features]
    y = df["modal_price"]

    # 80% train, 20% test
    split_index = int(len(df) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    print("Training records:", len(X_train))
    print("Testing records:", len(X_test))

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mape = mean_absolute_percentage_error(
        y_test,
        predictions
    ) * 100

    rmse = np.sqrt(
        mean_squared_error(y_test, predictions)
    )

    print("\n===== LAG-BASED FORECASTING RESULTS =====")
    print(f"MAPE: {mape:.2f}%")
    print(f"RMSE: {rmse:.2f}")

    print("\n===== NAIVE BASELINE =====")
    print("MAPE: 12.48%")
    print("RMSE: 196.21")

    print("\n===== COMPARISON =====")

    if mape < 12.48:
        print("✓ Forecasting model has better MAPE than baseline.")
    else:
        print("✗ Forecasting model does not beat baseline MAPE.")

    if rmse < 196.21:
        print("✓ Forecasting model has better RMSE than baseline.")
    else:
        print("✗ Forecasting model does not beat baseline RMSE.")


if __name__ == "__main__":
    evaluate_model()