-- Agricultural Market Intelligence
-- Star Schema

-- =========================
-- Dimension: Market
-- =========================

CREATE TABLE IF NOT EXISTS dim_market (
    market_id SERIAL PRIMARY KEY,
    market_name VARCHAR(150) UNIQUE NOT NULL
);


-- =========================
-- Dimension: Commodity
-- =========================

CREATE TABLE IF NOT EXISTS dim_commodity (
    commodity_id SERIAL PRIMARY KEY,
    commodity_name VARCHAR(100) UNIQUE NOT NULL
);


-- =========================
-- Dimension: Date
-- =========================

CREATE TABLE IF NOT EXISTS dim_date (
    date_id SERIAL PRIMARY KEY,
    arrival_date DATE UNIQUE NOT NULL,
    day INTEGER,
    month INTEGER,
    year INTEGER
);


-- =========================
-- Fact: Market Prices
-- =========================

CREATE TABLE IF NOT EXISTS fact_market_prices (
    price_id SERIAL PRIMARY KEY,

    market_id INTEGER REFERENCES dim_market(market_id),
    commodity_id INTEGER REFERENCES dim_commodity(commodity_id),
    date_id INTEGER REFERENCES dim_date(date_id),

    variety VARCHAR(100),

    arrivals DECIMAL(12,3),

    minimum_price DECIMAL(12,2),
    maximum_price DECIMAL(12,2),
    modal_price DECIMAL(12,2)
);