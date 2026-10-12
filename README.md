# Olist E-Commerce Analytics

A Python and PostgreSQL project using the Brazilian E-Commerce Public Dataset by Olist. The pipeline loads CSV files into RAW tables, builds cleaned STAGING tables, creates an order-level MART, runs data-quality checks, and answers five business questions with SQL.

## Tech stack
- Python, pandas
- PostgreSQL, SQLAlchemy, psycopg2
- Matplotlib / Seaborn
- SQL CTEs and window functions

## Project structure
```text
olist-ecommerce-analytics/
├── charts/       # Generated charts
├── data/raw/     # Dataset CSVs (excluded from Git)
├── logs/         # Pipeline logs
├── report/       # Final PDF report and results
├── sql/          # Required analytical SQL and investigation queries
├── src/          # Python pipeline and chart scripts
├── .env          # Local credentials (must not be committed)
├── .gitignore
├── requirements.txt
└── README.md
```

## Dataset
Download the Brazilian E-Commerce Public Dataset by Olist:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Extract these CSV files into `data/raw/`:
- `olist_orders_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `product_category_name_translation.csv`

## Setup (Windows PowerShell)

### 1. Create and activate a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

If `requirements.txt` has not been created yet:
```powershell
pip install pandas sqlalchemy psycopg2-binary python-dotenv matplotlib seaborn
pip freeze > requirements.txt
```

### 3. Create the database
In PostgreSQL/pgAdmin, create a database named `olist_analytics`. Make sure PostgreSQL is running.

### 4. Configure `.env`
Create a `.env` file in the project root. Replace the password placeholder with your local PostgreSQL password. Never commit this file.
```dotenv
DB_USER=postgres
DB_PASSWORD=YOUR_LOCAL_POSTGRES_PASSWORD
DB_HOST=localhost
DB_PORT=5432
DB_NAME=olist_analytics
```

## Run the pipeline
From the project root, with `venv` activated:
```powershell
python src/pipeline.py
```

Pipeline stages:
1. Load CSVs into RAW tables.
2. Build STAGING tables.
3. Run critical pre-MART data-quality checks.
4. Build `mart_order_summary`.
5. Run post-MART checks.
6. Record warnings and pipeline progress in `logs/pipeline.log`.

RAW tables are replaced during ingestion, while STAGING and MART tables are rebuilt on each run. Critical data-quality failures stop the pipeline. Warnings are reported without stopping the run.

## Data-quality checks
The checks cover:
- Duplicate and null order IDs.
- Delivery dates earlier than purchase timestamps.
- Orders without matching customers.
- Negative item/freight values.
- Review scores outside the valid 1–5 range.
- Multiple reviews for one order.
- Delivered orders missing a delivery timestamp.
- Payment totals differing from item price plus freight.

The current design treats duplicate/null IDs, invalid dates, missing customer relationships, negative values and invalid review scores as critical checks. Multiple reviews, missing delivery dates and payment reconciliation differences are warnings. Payment mismatches are flagged for investigation rather than automatically deleted or assumed to be invalid.

## SQL analyses
- `01_monthly_revenue.sql` — monthly merchandise value and month-over-month growth using `LAG()`.
- `02_top_categories_by_state.sql` — top product categories per customer state using `DENSE_RANK()`.
- `03_rolling_7_day_orders.sql` — daily order count and seven-day rolling average.
- `04_repeat_purchase_rate.sql` — repeat customers divided by unique customers.
- `05_delivery_delay_review.sql` — delivery-delay groups and review scores.
- `06_state_late_delivery.sql` — late-delivery comparisons by state.
- `07_payment_reconciliation.sql` — order-level payment reconciliation.
- `08_payment_installment_investigation.sql` — exploratory check of installment/payment patterns.

## Metric definitions
- **Merchandise value:** `SUM(order_items.price)`; freight and payment values are excluded.
- **Delivery delay:** actual customer delivery timestamp minus estimated delivery timestamp, in days. Negative values indicate early delivery.
- **Late delivery:** actual delivery is later than the estimated timestamp.
- **Repeat customer:** a `customer_unique_id` with more than one order in the mart. The current query does not filter order status, so interpret the rate using that population.
- **Review selection:** one review is retained per order by latest `review_answer_timestamp`, with `review_id` as a tie-breaker.

## Generate charts and report
```powershell
python src/create_charts.py
```
Chart images are saved in `charts/`. Save the final PDF in `report/` before submission.

## Troubleshooting
- **Database connection error:** check PostgreSQL is running, the database exists, and `.env` values are correct.
- **Missing CSV:** verify files are extracted to `data/raw/` and match the filenames in `src/config.py`.
- **Missing package:** activate `venv` and run `pip install -r requirements.txt`.
- **Pipeline issue:** review terminal output and `logs/pipeline.log`.

## Git safety
Do not commit `.env`, `venv/`, or `data/raw/`. Check `.gitignore` before pushing. This README does not contain database credentials.

## Data source
Olist, *Brazilian E-Commerce Public Dataset by Olist*, Kaggle:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
