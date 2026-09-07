import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

INPUT_FILE = "data/processed/mandi_prices_clean.csv"
MODEL_FILE = "ml/forecasting/price_model.pkl"


def train_model():

    print("Loading data...")

    df = pd.read_csv(INPUT_FILE)

    df["arrival_date"] = pd.to_datetime(df["arrival_date"])

    # Create time-based features
    df["day"] = df["arrival_date"].dt.day
    df["month"] = df["arrival_date"].dt.month
    df["year"] = df["arrival_date"].dt.year

    # Convert market names into numerical codes
    df["market_code"] = df["market"].astype("category").cat.codes

    # Features
    X = df[
        [
            "day",
            "month",
            "year",
            "market_code",
            "arrivals",
            "minimum_price",
            "maximum_price",
        ]
    ]

    # Target
    y = df["modal_price"]

    print("Training model...")

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    model.fit(X, y)

    joblib.dump(model, MODEL_FILE)

    print("\nModel trained successfully!")
    print("Model saved to:", MODEL_FILE)


if __name__ == "__main__":
    train_model()