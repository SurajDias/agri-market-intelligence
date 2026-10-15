\# Official Market Data Integration and ETL Validation



\## 1. Objective

To validate agricultural market-price records before database ingestion and improve data quality and duplicate prevention.



\## 2. ETL Validation

The ETL validation process checks:

\- Required columns and missing values

\- Invalid arrival dates

\- Nonnumeric and negative prices

\- Minimum, maximum and modal price consistency

\- Duplicate market-date-variety observations



Invalid records are separated and saved to `data/processed/mandi\_prices\_rejected.csv`, with rejection reasons.



\## 3. Database Design

The PostgreSQL database uses four tables:

\- `dim\_market`

\- `dim\_commodity`

\- `dim\_date`

\- `fact\_market\_prices`



The fact table has a unique constraint named `uq\_market\_price\_observation` on market, commodity, date and variety.



\## 4. Testing Results

\- ETL validation tests: 7 passed

\- Database constraint test: 1 passed

\- Total: 8 passed

\- Skipped tests: 0



\## 5. Data Provenance and Safety

The AGMARKNET API request returned a CAPTCHA/token-required error. Therefore, the provenance of the current CSV has not been verified as official source data.



Database ingestion remains disabled until the source and data provenance are verified.



\## 6. Future Work

\- Verify official source provenance and retrieval metadata.

\- Test repeated ingestion against the isolated test database.

\- Validate market, commodity and price-unit mappings.

\- Re-run the complete test suite after changes.

