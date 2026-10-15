
import pandas as pd
import pytest

from etl.load import validate_data


def valid_record():
    return {
        "market": "Test Market",
        "arrival_date": "05/09/2026",
        "arrivals": 100,
        "variety": "Tomato",
        "minimum_price": 1000,
        "maximum_price": 1500,
        "modal_price": 1200,
    }


def test_valid_record_is_accepted():
    accepted, rejected = validate_data(pd.DataFrame([valid_record()]))

    assert len(accepted) == 1
    assert len(rejected) == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("market", None),
        ("arrival_date", "not-a-date"),
        ("minimum_price", -10),
        ("modal_price", "not-a-number"),
        ("maximum_price", 900),
    ],
)
def test_invalid_records_are_rejected(field, value):
    record = valid_record()
    record[field] = value

    accepted, rejected = validate_data(pd.DataFrame([record]))

    assert len(accepted) == 0
    assert len(rejected) == 1
    assert rejected["rejection_reason"].notna().all()


def test_duplicate_records_are_rejected():
    record = valid_record()
    df = pd.DataFrame([record, record])

    accepted, rejected = validate_data(df)

    assert len(accepted) == 1
    assert len(rejected) == 1
    assert "Duplicate observation" in rejected.iloc[0]["rejection_reason"]
