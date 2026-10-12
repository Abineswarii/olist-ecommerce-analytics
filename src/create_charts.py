import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import text

from database import get_engine


engine = get_engine()


# ============================================================
# CHART 1 — MONTHLY MERCHANDISE REVENUE
# ============================================================

monthly_revenue_query = """
WITH month_series AS (
    SELECT
        generate_series(
            DATE_TRUNC(
                'month',
                (SELECT MIN(purchase_timestamp)
                 FROM mart_order_summary)
            ),
            DATE_TRUNC(
                'month',
                (SELECT MAX(purchase_timestamp)
                 FROM mart_order_summary)
            ),
            INTERVAL '1 month'
        ) AS month
),

monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', purchase_timestamp) AS month,
        SUM(COALESCE(item_value, 0)) AS revenue
    FROM mart_order_summary
    GROUP BY DATE_TRUNC('month', purchase_timestamp)
)

SELECT
    m.month,
    COALESCE(r.revenue, 0) AS revenue
FROM month_series m
LEFT JOIN monthly_revenue r
    ON m.month = r.month
ORDER BY m.month;
"""


monthly_df = pd.read_sql(
    text(monthly_revenue_query),
    engine
)

monthly_df["month"] = pd.to_datetime(monthly_df["month"])


plt.figure(figsize=(10, 5))

plt.plot(
    monthly_df["month"],
    monthly_df["revenue"],
    marker="o"
)

plt.title("Monthly Merchandise Revenue")
plt.xlabel("Month")
plt.ylabel("Revenue (BRL)")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    "charts/monthly_revenue.png",
    dpi=300
)

plt.close()


# ============================================================
# CHART 2 — DAILY ORDERS + 7-DAY ROLLING AVERAGE
# ============================================================

rolling_query = """
WITH calendar AS (
    SELECT
        generate_series(
            (
                SELECT MIN(DATE(purchase_timestamp))
                FROM mart_order_summary
            ),
            (
                SELECT MAX(DATE(purchase_timestamp))
                FROM mart_order_summary
            ),
            INTERVAL '1 day'
        )::date AS order_date
),

daily_orders AS (
    SELECT
        DATE(purchase_timestamp) AS order_date,
        COUNT(DISTINCT order_id) AS daily_order_count
    FROM mart_order_summary
    GROUP BY DATE(purchase_timestamp)
),

filled_daily_orders AS (
    SELECT
        c.order_date,
        COALESCE(d.daily_order_count, 0) AS daily_order_count
    FROM calendar c
    LEFT JOIN daily_orders d
        ON c.order_date = d.order_date
)

SELECT
    order_date,
    daily_order_count,

    AVG(daily_order_count) OVER (
        ORDER BY order_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7_day_average

FROM filled_daily_orders

ORDER BY order_date;
"""


rolling_df = pd.read_sql(
    text(rolling_query),
    engine
)

rolling_df["order_date"] = pd.to_datetime(
    rolling_df["order_date"]
)


plt.figure(figsize=(10, 5))

plt.plot(
    rolling_df["order_date"],
    rolling_df["daily_order_count"],
    linewidth=0.8,
    alpha=0.4,
    label="Daily Orders"
)

plt.plot(
    rolling_df["order_date"],
    rolling_df["rolling_7_day_average"],
    linewidth=2,
    label="7-Day Rolling Average"
)

plt.title("Daily Orders and 7-Day Rolling Average")
plt.xlabel("Date")
plt.ylabel("Orders")
plt.legend()
plt.tight_layout()

plt.savefig(
    "charts/rolling_7_day_orders.png",
    dpi=300
)

plt.close()


# ============================================================
# CHART 3 — DELIVERY DELAY VS REVIEW SCORE
# ============================================================

delivery_query = """
SELECT
    CASE
        WHEN delivery_delay_days < -7
            THEN 'More than 7 days early'

        WHEN delivery_delay_days >= -7
             AND delivery_delay_days < 0
            THEN '1–7 days early'

        WHEN delivery_delay_days = 0
            THEN 'On time'

        WHEN delivery_delay_days > 0
             AND delivery_delay_days <= 7
            THEN '1–7 days late'

        WHEN delivery_delay_days > 7
            THEN 'More than 7 days late'
    END AS delivery_status,

    AVG(review_score) AS average_review_score

FROM mart_order_summary

WHERE review_score IS NOT NULL
  AND delivery_delay_days IS NOT NULL

GROUP BY
    CASE
        WHEN delivery_delay_days < -7
            THEN 'More than 7 days early'

        WHEN delivery_delay_days >= -7
             AND delivery_delay_days < 0
            THEN '1–7 days early'

        WHEN delivery_delay_days = 0
            THEN 'On time'

        WHEN delivery_delay_days > 0
             AND delivery_delay_days <= 7
            THEN '1–7 days late'

        WHEN delivery_delay_days > 7
            THEN 'More than 7 days late'
    END;
"""


delivery_df = pd.read_sql(
    text(delivery_query),
    engine
)


order = [
    "More than 7 days early",
    "1–7 days early",
    "On time",
    "1–7 days late",
    "More than 7 days late"
]

delivery_df["delivery_status"] = pd.Categorical(
    delivery_df["delivery_status"],
    categories=order,
    ordered=True
)

delivery_df = delivery_df.sort_values(
    "delivery_status"
)


plt.figure(figsize=(9, 5))

plt.bar(
    delivery_df["delivery_status"],
    delivery_df["average_review_score"]
)

plt.title("Delivery Timing vs Average Review Score")
plt.xlabel("Delivery Status")
plt.ylabel("Average Review Score")
plt.xticks(rotation=20)
plt.ylim(0, 5)
plt.tight_layout()

plt.savefig(
    "charts/delivery_delay_review.png",
    dpi=300
)

plt.close()


# ============================================================
# CHART 4 — FIRST-ORDER DELIVERY VS REPEAT PURCHASE
# ============================================================

repeat_query = """
WITH first_orders AS (
    SELECT
        customer_unique_id,
        order_id,
        delivery_delay_days,

        ROW_NUMBER() OVER (
            PARTITION BY customer_unique_id
            ORDER BY purchase_timestamp
        ) AS order_sequence

    FROM mart_order_summary

    WHERE customer_unique_id IS NOT NULL
),

customer_repeat AS (
    SELECT
        customer_unique_id,
        COUNT(DISTINCT order_id) AS order_count

    FROM mart_order_summary

    WHERE customer_unique_id IS NOT NULL

    GROUP BY customer_unique_id
),

first_order_groups AS (
    SELECT
        f.customer_unique_id,

        CASE
            WHEN f.delivery_delay_days > 0
                THEN 'Late'

            WHEN f.delivery_delay_days <= 0
                THEN 'On Time / Early'

            ELSE 'Unknown'
        END AS first_order_delivery_status,

        c.order_count

    FROM first_orders f

    JOIN customer_repeat c
        ON f.customer_unique_id = c.customer_unique_id

    WHERE f.order_sequence = 1
)

SELECT
    first_order_delivery_status,

    100.0 *
    COUNT(*) FILTER (
        WHERE order_count > 1
    )
    / NULLIF(COUNT(*), 0)
    AS repeat_purchase_rate

FROM first_order_groups

WHERE first_order_delivery_status <> 'Unknown'

GROUP BY first_order_delivery_status;
"""


repeat_df = pd.read_sql(
    text(repeat_query),
    engine
)


order = [
    "Late",
    "On Time / Early"
]

repeat_df["first_order_delivery_status"] = pd.Categorical(
    repeat_df["first_order_delivery_status"],
    categories=order,
    ordered=True
)

repeat_df = repeat_df.sort_values(
    "first_order_delivery_status"
)


plt.figure(figsize=(7, 5))

plt.bar(
    repeat_df["first_order_delivery_status"],
    repeat_df["repeat_purchase_rate"]
)

plt.title(
    "First-Order Delivery Status vs Repeat Purchase Rate"
)

plt.xlabel("First-Order Delivery Status")
plt.ylabel("Repeat Purchase Rate (%)")
plt.ylim(0, 4)
plt.tight_layout()

plt.savefig(
    "charts/first_order_repeat_rate.png",
    dpi=300
)

plt.close()


print("\n======================================")
print("       CHARTS CREATED SUCCESSFULLY")
print("======================================")

print("charts/monthly_revenue.png")
print("charts/rolling_7_day_orders.png")
print("charts/delivery_delay_review.png")
print("charts/first_order_repeat_rate.png")