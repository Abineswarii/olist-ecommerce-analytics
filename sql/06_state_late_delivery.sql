-- Compare late-delivery performance across RJ, BA, SP, AL and MA.
-- Late = delivered after the estimated delivery timestamp.

SELECT
    customer_state,

    COUNT(*) FILTER (
        WHERE delivered_timestamp IS NOT NULL
          AND estimated_delivery_timestamp IS NOT NULL
    ) AS delivered_orders,

    COUNT(*) FILTER (
        WHERE delivery_delay_days > 0
    ) AS late_orders,

    ROUND(
        (
            100.0 * COUNT(*) FILTER (
                WHERE delivery_delay_days > 0
            )
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE delivery_delay_days IS NOT NULL
                ),
                0
            )
        )::numeric,
        2
    ) AS late_rate_percentage

FROM mart_order_summary
WHERE customer_state IN ('RJ', 'BA', 'SP', 'AL', 'MA')
GROUP BY customer_state
ORDER BY customer_state;