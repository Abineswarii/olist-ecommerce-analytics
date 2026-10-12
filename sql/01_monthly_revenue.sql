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
),

complete_months AS (
    SELECT
        m.month,
        COALESCE(r.revenue, 0) AS revenue
    FROM month_series m
    LEFT JOIN monthly_revenue r
        ON m.month = r.month
),

revenue_with_previous AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (
            ORDER BY month
        ) AS previous_month_revenue
    FROM complete_months
)

SELECT
    month,
    ROUND(revenue::numeric, 2) AS revenue,
    ROUND(previous_month_revenue::numeric, 2)
        AS previous_month_revenue,

    CASE
        WHEN previous_month_revenue IS NULL
             OR previous_month_revenue = 0
        THEN NULL
        ELSE ROUND(
            (
                100.0 *
                (revenue - previous_month_revenue)
                / previous_month_revenue
            )::numeric,
            2
        )
    END AS growth_percentage

FROM revenue_with_previous

ORDER BY month;