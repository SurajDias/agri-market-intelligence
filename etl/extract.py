import requests
import pandas as pd
import os

URL = "https://api.agmarknet.gov.in/v1/prices-and-arrivals/date-wise/specific-commodity"

params = {
    "year": 2026,
    "month": 9,
    "stateId": 16,
    "commodityId": 65,
    "includeExcel": "false"
}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://agmarknet.gov.in",
    "Referer": "https://agmarknet.gov.in/",
    "User-Agent": "Mozilla/5.0"
}


def extract_data():

    print("Fetching Tomato data from Karnataka...")

    response = requests.get(
        URL,
        params=params,
        headers=headers,
        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("success"):
        raise Exception("AGMARKNET returned an unsuccessful response")

    rows = []

    for market in result["markets"]:

        market_name = market["marketName"]

        for date_info in market["dates"]:

            arrival_date = date_info["arrivalDate"]

            for record in date_info["data"]:

                rows.append({
                    "market": market_name,
                    "arrival_date": arrival_date,
                    "arrivals": record.get("arrivals"),
                    "variety": record.get("variety"),
                    "minimum_price": record.get("minimumPrice"),
                    "maximum_price": record.get("maximumPrice"),
                    "modal_price": record.get("modalPrice")
                })

    df = pd.DataFrame(rows)

    return df


if __name__ == "__main__":

    df = extract_data()

    print("\nData extracted successfully!")

    print("Number of records:", len(df))

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 10 records:")
    print(df.head(10))

    # Create raw data folder
    os.makedirs("data/raw", exist_ok=True)

    # Save raw extracted data
    output_file = "data/raw/mandi_prices.csv"

    df.to_csv(output_file, index=False)

    print("\nData saved to:", output_file)