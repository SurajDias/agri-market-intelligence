
import os
import pandas as pd
from sqlalchemy import create_engine, text

INPUT_FILE = "data/processed/mandi_prices_clean.csv"

DB_URL = os.getenv(
    "AGRI_DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:5433/agri_market",
)

# Keep False until official source provenance is verified.
ALLOW_DATABASE_INGESTION = False


def validate_data(df):
    """Validate records and separate accepted and rejected rows."""

    required = [
        "market",
        "arrival_date",
        "minimum_price",
        "maximum_price",
        "modal_price",
        "variety",
    ]

    missing_columns = [col for col in required if col not in df.columns]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    df = df.copy()

    # Clean text columns
    df["market"] = df["market"].astype("string").str.strip()
    df["variety"] = df["variety"].astype("string").str.strip()

    # Convert dates
    df["arrival_date"] = pd.to_datetime(
        df["arrival_date"],
        errors="coerce",
        dayfirst=True,
    )

    # Convert numeric columns
    numeric_columns = [
        "minimum_price",
        "maximum_price",
        "modal_price",
        "arrivals",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

    # Store rejection reasons
    reasons = pd.Series(
        "",
        index=df.index,
        dtype="string",
    )

    def reject(mask, reason):
        mask = mask.fillna(False)

        reasons.loc[mask] = reasons.loc[mask].apply(
            lambda old: f"{old}; {reason}" if old else reason
        )

    # Required text and date validation
    reject(
        df["market"].isna() | df["market"].eq(""),
        "Missing market",
    )

    reject(
        df["variety"].isna() | df["variety"].eq(""),
        "Missing variety",
    )

    reject(
        df["arrival_date"].isna(),
        "Missing or invalid arrival date",
    )

    # Price validation
    for col in [
        "minimum_price",
        "maximum_price",
        "modal_price",
    ]:
        reject(
            df[col].isna(),
            f"Missing or invalid {col}",
        )

        reject(
            df[col].notna() & (df[col] < 0),
            f"Negative {col}",
        )

    # Minimum price must not exceed maximum price
    reject(
        df["minimum_price"].notna()
        & df["maximum_price"].notna()
        & (df["minimum_price"] > df["maximum_price"]),
        "Minimum price exceeds maximum price",
    )

    # Modal price must be within the minimum-maximum range
    reject(
        df["modal_price"].notna()
        & df["minimum_price"].notna()
        & (df["modal_price"] < df["minimum_price"]),
        "Modal price below minimum price",
    )

    reject(
        df["modal_price"].notna()
        & df["maximum_price"].notna()
        & (df["modal_price"] > df["maximum_price"]),
        "Modal price above maximum price",
    )

    # Separate invalid records
    rejected = df.loc[reasons.ne("")].copy()
    rejected["rejection_reason"] = reasons.loc[rejected.index]

    accepted = df.loc[reasons.eq("")].copy()

    # This loader assumes the file contains Tomato data only.
    # Add commodity mapping before using mixed-commodity data.
    accepted["commodity"] = "Tomato"

    # Identify duplicate observations
    duplicate_key = [
        "market",
        "arrival_date",
        "variety",
    ]

    duplicate_mask = accepted.duplicated(
        subset=duplicate_key,
        keep="first",
    )

    duplicates = accepted.loc[duplicate_mask].copy()

    if not duplicates.empty:
        duplicates["rejection_reason"] = (
            "Duplicate observation in input"
        )

        # Append duplicate records only when duplicates exist.
        rejected = pd.concat(
            [rejected, duplicates],
            ignore_index=True,
        )

    # Keep only the first occurrence of each observation
    accepted = accepted.loc[~duplicate_mask].copy()

    return accepted, rejected


def load_data():
    """Validate the CSV and optionally load records into PostgreSQL."""

    print("Reading cleaned data...")

    df = pd.read_csv(INPUT_FILE)

    print("Records read:", len(df))

    accepted, rejected = validate_data(df)

    os.makedirs("data/processed", exist_ok=True)

    rejected.to_csv(
        "data/processed/mandi_prices_rejected.csv",
        index=False,
    )

    print("Valid records:", len(accepted))
    print("Rejected records:", len(rejected))
    print(
        "Rejected-record report saved to "
        "data/processed/mandi_prices_rejected.csv"
    )

    # Safety guard: do not write to the database by default.
    if not ALLOW_DATABASE_INGESTION:
        print("\nDRY RUN: database ingestion is disabled.")
        print(
            "Verify official source provenance before enabling it."
        )
        return

    engine = create_engine(DB_URL)

    inserted_count = 0
    skipped_count = 0

    try:
        with engine.begin() as connection:

            for _, row in accepted.iterrows():

                # 1. Insert or retrieve market dimension
                result = connection.execute(
                    text("""
                        INSERT INTO dim_market (market_name)
                        VALUES (:market_name)
                        ON CONFLICT (market_name)
                        DO UPDATE SET
                            market_name = EXCLUDED.market_name
                        RETURNING market_id
                    """),
                    {
                        "market_name": row["market"],
                    },
                )

                market_id = result.scalar_one()

                # 2. Insert or retrieve commodity dimension
                result = connection.execute(
                    text("""
                        INSERT INTO dim_commodity (commodity_name)
                        VALUES (:commodity_name)
                        ON CONFLICT (commodity_name)
                        DO UPDATE SET
                            commodity_name = EXCLUDED.commodity_name
                        RETURNING commodity_id
                    """),
                    {
                        "commodity_name": row["commodity"],
                    },
                )

                commodity_id = result.scalar_one()

                # 3. Insert or retrieve date dimension
                arrival_date = row["arrival_date"].date()

                result = connection.execute(
                    text("""
                        INSERT INTO dim_date (
                            arrival_date,
                            day,
                            month,
                            year
                        )
                        VALUES (
                            :date,
                            :day,
                            :month,
                            :year
                        )
                        ON CONFLICT (arrival_date)
                        DO UPDATE SET
                            arrival_date = EXCLUDED.arrival_date
                        RETURNING date_id
                    """),
                    {
                        "date": arrival_date,
                        "day": arrival_date.day,
                        "month": arrival_date.month,
                        "year": arrival_date.year,
                    },
                )

                date_id = result.scalar_one()

                # 4. Insert fact record; skip existing observations
                result = connection.execute(
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
                        ON CONFLICT ON CONSTRAINT
                            uq_market_price_observation
                        DO NOTHING
                    """),
                    {
                        "market_id": market_id,
                        "commodity_id": commodity_id,
                        "date_id": date_id,
                        "variety": row["variety"],
                        "arrivals": (
                            row["arrivals"]
                            if "arrivals" in row.index
                            and pd.notna(row["arrivals"])
                            else None
                        ),
                        "minimum_price": row["minimum_price"],
                        "maximum_price": row["maximum_price"],
                        "modal_price": row["modal_price"],
                    },
                )

                if result.rowcount == 1:
                    inserted_count += 1
                else:
                    skipped_count += 1

    finally:
        engine.dispose()

    print("\nIngestion completed successfully.")
    print("New observations inserted:", inserted_count)
    print("Duplicate observations skipped:", skipped_count)


if __name__ == "__main__":
    load_data()

