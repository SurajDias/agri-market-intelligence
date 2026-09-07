import pandas as pd


INPUT_FILE = "data/raw/mandi_prices.csv"
OUTPUT_FILE = "data/processed/mandi_prices_clean.csv"


def transform_data():

    # Read raw data
    df = pd.read_csv(INPUT_FILE)

    print("Raw records:", len(df))

    # Convert date
    df["arrival_date"] = pd.to_datetime(
        df["arrival_date"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    # Convert numeric columns
    numeric_columns = [
        "arrivals",
        "minimum_price",
        "maximum_price",
        "modal_price"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Remove duplicate records
    df = df.drop_duplicates()

    # Remove records with missing important values
    df = df.dropna(
        subset=[
            "market",
            "arrival_date",
            "modal_price"
        ]
    )

    # Clean text columns
    df["market"] = df["market"].str.strip()
    df["variety"] = df["variety"].str.strip()

    print("Clean records:", len(df))

    return df


if __name__ == "__main__":

    df = transform_data()

    print("\nCleaned data:")
    print(df.head(10))

    print("\nData types:")
    print(df.dtypes)

    # Create processed folder
    import os
    os.makedirs("data/processed", exist_ok=True)

    # Save cleaned data
    df.to_csv(OUTPUT_FILE, index=False)

    print("\nCleaned data saved to:", OUTPUT_FILE)