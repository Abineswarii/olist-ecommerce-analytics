-- Investigate whether reconciliation differences vary
-- by payment type and installment count.
-- This query does not prove that installments cause mismatches.

WITH item_totals AS (
    SELECT
        order_id,
        SUM(price + freight_value) AS item_freight_total
    FROM stg_order_items
    GROUP BY order_id
),
payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_total,
        MAX(payment_installments) AS max_installments,
        STRING_AGG(
            DISTINCT payment_type,
            ', '
        ) AS payment_types
    FROM stg_order_payments
    GROUP BY order_id
),
reconciliation AS (
    SELECT
        p.order_id,
        p.payment_types,
        p.max_installments,
        p.payment_total,
        COALESCE(i.item_freight_total, 0)
            AS item_freight_total,
        p.payment_total
          - COALESCE(i.item_freight_total, 0)
            AS difference
    FROM payment_totals p
    LEFT JOIN item_totals i
        ON p.order_id = i.order_id
)
SELECT
    payment_types,
    max_installments,
    COUNT(*) AS orders_checked,

    COUNT(*) FILTER (
        WHERE ABS(difference) > 0.01
    ) AS mismatched_orders,

    ROUND(
        COALESCE(
            SUM(ABS(difference)) FILTER (
                WHERE ABS(difference) > 0.01
            ),
            0
        )::numeric,
        2
    ) AS absolute_difference_brl

FROM reconciliation
GROUP BY payment_types, max_installments
ORDER BY absolute_difference_brl DESC NULLS LAST;