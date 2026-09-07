import pandas as pd


INPUT_FILE = "data/processed/mandi_prices_clean.csv"


def check_data_quality():

    df = pd.read_csv(INPUT_FILE)

    print("========== DATA QUALITY REPORT ==========\n")

    # 1. Missing values
    print("1. Missing Values:")
    print(df.isnull().sum())

    # 2. Duplicate records
    duplicates = df.duplicated().sum()

    print("\n2. Duplicate Records:")
    print(duplicates)

    # 3. Invalid prices
    invalid_prices = df[
        (df["minimum_price"] < 0) |
        (df["maximum_price"] < 0) |
        (df["modal_price"] < 0)
    ]

    print("\n3. Invalid Price Records:")
    print(len(invalid_prices))

    # 4. Price consistency
    inconsistent_prices = df[
        (df["minimum_price"] > df["maximum_price"]) |
        (df["modal_price"] < df["minimum_price"]) |
        (df["modal_price"] > df["maximum_price"])
    ]

    print("\n4. Inconsistent Price Records:")
    print(len(inconsistent_prices))

    # 5. Outlier detection using IQR
    Q1 = df["modal_price"].quantile(0.25)
    Q3 = df["modal_price"].quantile(0.75)

    IQR = Q3 - Q1

    lower_limit = Q1 - 1.5 * IQR
    upper_limit = Q3 + 1.5 * IQR

    outliers = df[
        (df["modal_price"] < lower_limit) |
        (df["modal_price"] > upper_limit)
    ]

    print("\n5. Modal Price Outliers:")
    print(len(outliers))

    print("\n=========================================")


if __name__ == "__main__":
    check_data_quality()