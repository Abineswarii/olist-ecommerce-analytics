WITH delivery_groups AS (
    SELECT
        order_id,
        review_score,
        delivery_delay_days,

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

            ELSE 'Unknown'
        END AS delivery_status

    FROM mart_order_summary

    WHERE review_score IS NOT NULL
)

SELECT
    delivery_status,
    COUNT(*) AS order_count,
    ROUND(
        AVG(review_score)::numeric,
        2
    ) AS average_review_score

FROM delivery_groups

WHERE delivery_status <> 'Unknown'

GROUP BY delivery_status

ORDER BY
    CASE delivery_status
        WHEN 'More than 7 days early' THEN 1
        WHEN '1–7 days early' THEN 2
        WHEN 'On time' THEN 3
        WHEN '1–7 days late' THEN 4
        WHEN 'More than 7 days late' THEN 5
    END;