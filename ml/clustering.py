import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

INPUT_FILE = "data/processed/mandi_prices_clean.csv"


def perform_clustering():

    print("Loading data...")

    df = pd.read_csv(INPUT_FILE)

    # Create market-level features
    market_features = df.groupby("market").agg(
        average_price=("modal_price", "mean"),
        minimum_price=("modal_price", "min"),
        maximum_price=("modal_price", "max"),
        price_std=("modal_price", "std"),
        average_arrivals=("arrivals", "mean")
    ).reset_index()

    # Replace missing standard deviation with 0
    market_features["price_std"] = (
        market_features["price_std"].fillna(0)
    )

    features = [
        "average_price",
        "minimum_price",
        "maximum_price",
        "price_std",
        "average_arrivals"
    ]

    # Standardize features
    scaler = StandardScaler()
    X = scaler.fit_transform(market_features[features])

    # Create 3 market clusters
    model = KMeans(
        n_clusters=3,
        random_state=42,
        n_init=10
    )

    market_features["cluster"] = model.fit_predict(X)

    print("\n===== MARKET CLUSTERS =====")
    print(
        market_features[
            ["market", "average_price", "price_std", "average_arrivals", "cluster"]
        ].sort_values("cluster")
    )

    # Save results
    output_file = "data/processed/market_clusters.csv"
    market_features.to_csv(output_file, index=False)

    print("\nClustering completed successfully!")
    print("Results saved to:", output_file)


if __name__ == "__main__":
    perform_clustering()