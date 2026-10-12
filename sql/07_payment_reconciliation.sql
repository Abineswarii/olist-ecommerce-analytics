-- Investigate payment reconciliation at order level.
-- Difference = payment total - item value - freight.
-- A mismatch is a flag, not proof of an invalid transaction.

WITH item_totals AS (
    SELECT
        order_id,
        SUM(price) AS item_value,
        SUM(freight_value) AS freight_value
    FROM stg_order_items
    GROUP BY order_id
),
payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value
    FROM stg_order_payments
    GROUP BY order_id
),
reconciliation AS (
    SELECT
        COALESCE(i.order_id, p.order_id) AS order_id,
        COALESCE(i.item_value, 0) AS item_value,
        COALESCE(i.freight_value, 0) AS freight_value,
        COALESCE(p.payment_value, 0) AS payment_value,
        COALESCE(p.payment_value, 0)
          - COALESCE(i.item_value, 0)
          - COALESCE(i.freight_value, 0) AS difference
    FROM item_totals i
    FULL OUTER JOIN payment_totals p
        ON i.order_id = p.order_id
)
SELECT
    COUNT(*) AS total_orders_checked,

    COUNT(*) FILTER (
        WHERE ABS(difference) <= 0.01
    ) AS reconciled_orders,

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
    ) AS total_absolute_difference_brl

FROM reconciliation;