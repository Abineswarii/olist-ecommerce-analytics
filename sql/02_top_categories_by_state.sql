-- Q2: Top 3 product categories by customer state
-- Revenue = SUM of item prices, excluding freight.

WITH category_sales AS (
    SELECT
        c.customer_state,
        COALESCE(
            t.product_category_name_english,
            p.product_category_name,
            'Unknown'
        ) AS category,
        SUM(oi.price) AS revenue
    FROM stg_order_items oi
    JOIN stg_orders o
        ON oi.order_id = o.order_id
    JOIN stg_customers c
        ON o.customer_id = c.customer_id
    JOIN stg_products p
        ON oi.product_id = p.product_id
    LEFT JOIN stg_category_translation t
        ON p.product_category_name =
           t.product_category_name
    GROUP BY
        c.customer_state,
        COALESCE(
            t.product_category_name_english,
            p.product_category_name,
            'Unknown'
        )
),
ranked_categories AS (
    SELECT
        customer_state,
        category,
        revenue,
        DENSE_RANK() OVER (
            PARTITION BY customer_state
            ORDER BY revenue DESC
        ) AS category_rank
    FROM category_sales
)
SELECT
    customer_state,
    category_rank,
    category,
    ROUND(revenue::numeric, 2) AS revenue_brl
FROM ranked_categories
WHERE category_rank <= 3
ORDER BY
    customer_state,
    category_rank,
    revenue DESC;