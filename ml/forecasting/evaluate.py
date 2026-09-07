import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error

INPUT_FILE = "data/processed/mandi_prices_clean.csv"


def evaluate_model():

    print("Loading data...")

    df = pd.read_csv(INPUT_FILE)

    df["arrival_date"] = pd.to_datetime(df["arrival_date"])

    # Create time features
    df["day"] = df["arrival_date"].dt.day
    df["month"] = df["arrival_date"].dt.month
    df["year"] = df["arrival_date"].dt.year

    # Convert market to numerical code
    df["market_code"] = df["market"].astype("category").cat.codes

    # Sort chronologically
    df = df.sort_values("arrival_date")

    features = [
        "day",
        "month",
        "year",
        "market_code",
        "arrivals",
        "minimum_price",
        "maximum_price",
    ]

    X = df[features]
    y = df["modal_price"]

    # 80% training, 20% testing
    split_index = int(len(df) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    print("Training records:", len(X_train))
    print("Testing records:", len(X_test))

    # Train model on training data only
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    model.fit(X_train, y_train)

    # Predict test data
    predictions = model.predict(X_test)

    # Calculate metrics
    mape = mean_absolute_percentage_error(
        y_test, predictions
    ) * 100

    rmse = np.sqrt(
        mean_squared_error(y_test, predictions)
    )

    print("\n===== FORECASTING MODEL RESULTS =====")
    print(f"MAPE: {mape:.2f}%")
    print(f"RMSE: {rmse:.2f}")

    print("\n===== BASELINE RESULTS =====")
    print("MAPE: 12.48%")
    print("RMSE: 196.21")

    print("\n===== COMPARISON =====")

    if mape < 12.48:
        print("Model has better MAPE than baseline.")
    else:
        print("Model does not beat baseline MAPE yet.")

    if rmse < 196.21:
        print("Model has better RMSE than baseline.")
    else:
        print("Model does not beat baseline RMSE yet.")


if __name__ == "__main__":
    evaluate_model()