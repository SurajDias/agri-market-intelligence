
import os
import pandas as pd

INPUT_FILE = "data/raw/mandi_prices.csv"
OUTPUT_FILE = "data/processed/mandi_prices_clean.csv"
REJECTED_FILE = "data/processed/mandi_prices_rejected.csv"

REQUIRED_COLUMNS = [
    "market",
    "arrival_date",
    "minimum_price",
    "maximum_price",
    "modal_price",
]


def transform_data():
    # Read raw data without changing the original file
    df = pd.read_csv(INPUT_FILE)
    print("Raw records:", len(df))

    # Check the input structure
    missing_columns = [
        col for col in REQUIRED_COLUMNS if col not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Input is missing required columns: {missing_columns}"
        )

    # Preserve original row numbers for rejection reporting
    df.insert(0, "source_row", range(2, len(df) + 2))

    # Normalize text fields safely
    for column in ["market", "variety", "commodity", "state", "unit"]:
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip()
            df[column] = df[column].replace("", pd.NA)

    # Parse dates; support common source formats
    df["arrival_date"] = pd.to_datetime(
        df["arrival_date"],
        errors="coerce",
        dayfirst=True,
    )

    # Parse numeric fields
    numeric_columns = [
        "arrivals",
        "minimum_price",
        "maximum_price",
        "modal_price",
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    # Record every validation failure with a clear reason
    rejection_reasons = pd.Series("", index=df.index, dtype="string")

    def reject_where(mask, reason):
        nonlocal rejection_reasons
        mask = mask.fillna(False)
        rejection_reasons.loc[mask] = rejection_reasons.loc[mask].apply(
            lambda old: f"{old}; {reason}" if old else reason
        )

    # Required fields
    reject_where(df["market"].isna(), "Missing market")
    reject_where(df["arrival_date"].isna(), "Missing or invalid arrival date")

    for column in ["minimum_price", "maximum_price", "modal_price"]:
        reject_where(df[column].isna(), f"Missing or invalid {column}")

    # Prices must be non-negative
    for column in ["minimum_price", "maximum_price", "modal_price"]:
        reject_where(
            df[column].notna() & (df[column] < 0),
            f"Negative {column}",
        )

    # Basic price consistency
    reject_where(
        df["minimum_price"].notna()
        & df["maximum_price"].notna()
        & (df["minimum_price"] > df["maximum_price"]),
        "Minimum price exceeds maximum price",
    )

    reject_where(
        df["modal_price"].notna()
        & df["minimum_price"].notna()
        & (df["modal_price"] < df["minimum_price"]),
        "Modal price below minimum price",
    )

    reject_where(
        df["modal_price"].notna()
        & df["maximum_price"].notna()
        & (df["modal_price"] > df["maximum_price"]),
        "Modal price above maximum price",
    )

    # Unknown units should be reviewed if a unit column exists.
    # Do not convert prices unless the source unit is known.
    if "unit" in df.columns:
        known_units = {
            "quintal", "quintals", "rs/quintal", "inr/quintal",
            "₹/quintal", "kg", "kilogram", "rs/kg", "inr/kg", "₹/kg"
        }
        normalized_units = df["unit"].str.lower()
        reject_where(
            normalized_units.isna()
            | ~normalized_units.isin(known_units),
            "Missing or unknown price unit",
        )

    # Split rejected and potentially valid records
    rejected = df[rejection_reasons.ne("")].copy()
    rejected["rejection_reason"] = rejection_reasons.loc[rejected.index]

    accepted = df[rejection_reasons.eq("")].copy()

    # Detect duplicate observations in the accepted set.
    # Use the available identifying columns; do not silently merge
    # records that differ by variety or grade.
    key_columns = [
        col for col in [
            "market", "arrival_date", "variety", "grade",
            "commodity", "state", "unit",
            "minimum_price", "maximum_price", "modal_price", "arrivals"
        ]
        if col in accepted.columns
    ]

    duplicate_mask = accepted.duplicated(
        subset=key_columns, keep="first"
    )
    duplicate_rows = accepted.loc[duplicate_mask].copy()
    duplicate_rows["rejection_reason"] = "Duplicate observation"
    rejected = pd.concat([rejected, duplicate_rows], ignore_index=True)
    accepted = accepted.loc[~duplicate_mask].copy()

    # Remove the internal source row from accepted output
    accepted = accepted.drop(columns=["source_row"])

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    accepted.to_csv(OUTPUT_FILE, index=False)
    rejected.to_csv(REJECTED_FILE, index=False)

    print("Accepted records:", len(accepted))
    print("Rejected records:", len(rejected))
    print("Accepted data saved to:", OUTPUT_FILE)
    print("Rejected data saved to:", REJECTED_FILE)

    if not rejected.empty:
        print("\nRejection reasons:")
        print(rejected["rejection_reason"].value_counts())

    return accepted


if __name__ == "__main__":
    transform_data()
