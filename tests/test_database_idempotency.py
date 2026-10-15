
import os
import uuid
import pytest
from sqlalchemy import create_engine, text


@pytest.fixture
def test_engine():
    database_url = os.getenv("AGRI_TEST_DATABASE_URL")

    if not database_url:
        pytest.skip(
            "Set AGRI_TEST_DATABASE_URL to an isolated test database"
        )

    # Safety check: never run these tests against production.
    if not database_url.rstrip("/").endswith("agri_market_test"):
        pytest.fail(
            "Safety check failed: use only the agri_market_test database"
        )

    engine = create_engine(database_url)

    try:
        yield engine
    finally:
        engine.dispose()


def test_market_price_unique_constraint_exists(test_engine):
    with test_engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM pg_constraint
                WHERE conrelid = 'public.fact_market_prices'::regclass
                  AND conname = 'uq_market_price_observation'
                  AND contype = 'u'
            """)
        ).scalar_one()

    assert result == 1


def test_duplicate_observation_is_prevented(test_engine):
    # Use a transaction and roll it back so test records are not retained.
    with test_engine.connect() as connection:
        transaction = connection.begin()

        try:
            suffix = uuid.uuid4().hex[:12]

            market_id = connection.execute(
                text("""
                    INSERT INTO dim_market (market_name)
                    VALUES (:name)
                    RETURNING market_id
                """),
                {"name": f"pytest_market_{suffix}"},
            ).scalar_one()

            commodity_id = connection.execute(
                text("""
                    INSERT INTO dim_commodity (commodity_name)
                    VALUES (:name)
                    RETURNING commodity_id
                """),
                {"name": f"pytest_commodity_{suffix}"},
            ).scalar_one()

            date_id = connection.execute(
                text("""
                    INSERT INTO dim_date (arrival_date, day, month, year)
                    VALUES (DATE '2099-01-01', 1, 1, 2099)
                    ON CONFLICT (arrival_date)
                    DO UPDATE SET arrival_date = EXCLUDED.arrival_date
                    RETURNING date_id
                """)
            ).scalar_one()

            insert_sql = text("""
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
                ON CONFLICT ON CONSTRAINT uq_market_price_observation
                DO NOTHING
            """)

            values = {
                "market_id": market_id,
                "commodity_id": commodity_id,
                "date_id": date_id,
                "variety": "pytest_test_variety",
                "arrivals": None,
                "minimum_price": 100,
                "maximum_price": 200,
                "modal_price": 150,
            }

            first_insert = connection.execute(insert_sql, values)
            second_insert = connection.execute(insert_sql, values)

            assert first_insert.rowcount == 1
            assert second_insert.rowcount == 0

            count = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM fact_market_prices
                    WHERE market_id = :market_id
                      AND commodity_id = :commodity_id
                      AND date_id = :date_id
                      AND variety = :variety
                """),
                {
                    "market_id": market_id,
                    "commodity_id": commodity_id,
                    "date_id": date_id,
                    "variety": "pytest_test_variety",
                },
            ).scalar_one()

            assert count == 1

        finally:
            transaction.rollback()



