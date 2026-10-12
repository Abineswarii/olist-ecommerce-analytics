from sqlalchemy import text

from database import get_engine


def build_mart_tables():

    engine = get_engine()

    with engine.begin() as connection:

        print("Building mart_order_summary...")

        connection.execute(text("""
            DROP TABLE IF EXISTS mart_order_summary;

            CREATE TABLE mart_order_summary AS

            WITH item_summary AS (
                SELECT
                    order_id,
                    SUM(price) AS item_value,
                    SUM(freight_value) AS freight_value
                FROM stg_order_items
                GROUP BY order_id
            ),

            payment_summary AS (
                SELECT
                    order_id,
                    SUM(payment_value) AS payment_value
                FROM stg_order_payments
                GROUP BY order_id
            ),

            review_summary AS (
                SELECT
                    order_id,
                    review_score
                FROM (
                    SELECT
                        order_id,
                        review_score,

                        ROW_NUMBER() OVER (
                            PARTITION BY order_id
                            ORDER BY
                                review_answer_timestamp DESC NULLS LAST,
                                review_id DESC
                        ) AS rn

                    FROM stg_order_reviews
                ) ranked_reviews

                WHERE rn = 1
            )

            SELECT
                o.order_id,

                c.customer_unique_id,
                c.customer_city,
                c.customer_state,

                o.order_status,

                o.order_purchase_timestamp AS purchase_timestamp,
                o.order_approved_at AS approved_timestamp,
                o.order_delivered_carrier_date AS delivered_carrier_timestamp,
                o.order_delivered_customer_date AS delivered_timestamp,
                o.order_estimated_delivery_date AS estimated_delivery_timestamp,

                i.item_value,
                i.freight_value,

                COALESCE(p.payment_value, 0) AS payment_value,

                r.review_score,

                /*
                 * Payment reconciliation
                 *
                 * Difference between the recorded payment amount
                 * and item value + freight value.
                 *
                 * A tolerance of BRL 0.01 is used.
                 */
                (
                    COALESCE(p.payment_value, 0)
                    -
                    (
                        COALESCE(i.item_value, 0)
                        +
                        COALESCE(i.freight_value, 0)
                    )
                ) AS payment_reconciliation_difference,

                CASE
                    WHEN ABS(
                        COALESCE(p.payment_value, 0)
                        -
                        (
                            COALESCE(i.item_value, 0)
                            +
                            COALESCE(i.freight_value, 0)
                        )
                    ) > 0.01
                    THEN 1
                    ELSE 0
                END AS payment_reconciliation_flag,

                CASE
                    WHEN o.order_delivered_customer_date IS NOT NULL
                    THEN
                        EXTRACT(
                            EPOCH FROM
                            (
                                o.order_delivered_customer_date
                                - o.order_purchase_timestamp
                            )
                        ) / 86400.0
                END AS delivery_days,

                CASE
                    WHEN
                        o.order_delivered_customer_date IS NOT NULL
                        AND o.order_estimated_delivery_date IS NOT NULL
                    THEN
                        EXTRACT(
                            EPOCH FROM
                            (
                                o.order_delivered_customer_date
                                - o.order_estimated_delivery_date
                            )
                        ) / 86400.0
                END AS delivery_delay_days

            FROM stg_orders o

            LEFT JOIN stg_customers c
                ON o.customer_id = c.customer_id

            LEFT JOIN item_summary i
                ON o.order_id = i.order_id

            LEFT JOIN payment_summary p
                ON o.order_id = p.order_id

            LEFT JOIN review_summary r
                ON o.order_id = r.order_id;
        """))

        print("mart_order_summary created successfully.")


if __name__ == "__main__":
    build_mart_tables()