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

    ROUND(
        AVG(daily_order_count) OVER (
            ORDER BY order_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::numeric,
        2
    ) AS rolling_7_day_average

FROM filled_daily_orders

ORDER BY order_date;