import pandas as pd
from sqlalchemy import create_engine, text

INPUT_FILE = "data/processed/mandi_prices_clean.csv"

DB_URL = "postgresql://postgres:postgres@127.0.0.1:5433/agri_market"
def load_data():

    print("Reading cleaned data...")

    df = pd.read_csv(INPUT_FILE)

    # Connect to PostgreSQL
    engine = create_engine(DB_URL)

    print("Connected to PostgreSQL!")

    with engine.begin() as connection:

        for _, row in df.iterrows():

            # -------------------------
            # MARKET DIMENSION
            # -------------------------
            result = connection.execute(
                text("""
                    INSERT INTO dim_market (market_name)
                    VALUES (:market_name)
                    ON CONFLICT (market_name)
                    DO UPDATE SET market_name = EXCLUDED.market_name
                    RETURNING market_id
                """),
                {
                    "market_name": row["market"]
                }
            )

            market_id = result.fetchone()[0]

            # -------------------------
            # COMMODITY DIMENSION
            # -------------------------
            result = connection.execute(
                text("""
                    INSERT INTO dim_commodity (commodity_name)
                    VALUES ('Tomato')
                    ON CONFLICT (commodity_name)
                    DO UPDATE SET commodity_name = EXCLUDED.commodity_name
                    RETURNING commodity_id
                """)
            )

            commodity_id = result.fetchone()[0]

            # -------------------------
            # DATE DIMENSION
            # -------------------------
            arrival_date = pd.to_datetime(row["arrival_date"])

            result = connection.execute(
                text("""
                    INSERT INTO dim_date (
                        arrival_date,
                        day,
                        month,
                        year
                    )
                    VALUES (
                        :arrival_date,
                        :day,
                        :month,
                        :year
                    )
                    ON CONFLICT (arrival_date)
                    DO UPDATE SET arrival_date = EXCLUDED.arrival_date
                    RETURNING date_id
                """),
                {
                    "arrival_date": arrival_date.date(),
                    "day": arrival_date.day,
                    "month": arrival_date.month,
                    "year": arrival_date.year
                }
            )

            date_id = result.fetchone()[0]

            # -------------------------
            # FACT TABLE
            # -------------------------
            connection.execute(
                text("""
                    INSERT INTO fact_market_prices (
                        market_id,
                        commodity_id,
                        date_id,
                        variety,
                        arrivals,
                        minimum_price,
                        maximum_price,
                        modal_price
                    )
                    VALUES (
                        :market_id,
                        :commodity_id,
                        :date_id,
                        :variety,
                        :arrivals,
                        :minimum_price,
                        :maximum_price,
                        :modal_price
                    )
                """),
                {
                    "market_id": market_id,
                    "commodity_id": commodity_id,
                    "date_id": date_id,
                    "variety": row["variety"],
                    "arrivals": row["arrivals"],
                    "minimum_price": row["minimum_price"],
                    "maximum_price": row["maximum_price"],
                    "modal_price": row["modal_price"]
                }
            )

    print(f"\nSuccessfully loaded {len(df)} records into PostgreSQL!")


if __name__ == "__main__":
    load_data()