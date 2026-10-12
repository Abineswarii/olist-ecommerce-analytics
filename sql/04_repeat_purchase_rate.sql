WITH customer_orders AS (
    SELECT
        customer_unique_id,
        COUNT(DISTINCT order_id) AS order_count
    FROM mart_order_summary
    WHERE customer_unique_id IS NOT NULL
    GROUP BY customer_unique_id
),

customer_summary AS (
    SELECT
        COUNT(*) AS total_customers,

        COUNT(*) FILTER (
            WHERE order_count > 1
        ) AS repeat_customers

    FROM customer_orders
)

SELECT
    total_customers,
    repeat_customers,

    ROUND(
        (
            100.0 * repeat_customers
            / NULLIF(total_customers, 0)
        )::numeric,
        2
    ) AS repeat_purchase_rate_percentage

FROM customer_summary;