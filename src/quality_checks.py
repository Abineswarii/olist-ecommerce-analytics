from sqlalchemy import text
from database import get_engine


# ============================================================
# PRE-MART QUALITY CHECKS
# These checks are critical.
# If any of them fail, the pipeline stops before MART creation.
# ============================================================

def run_pre_mart_quality_checks():

    engine = get_engine()

    checks = [
        (
            "Duplicate order IDs",
            """
            SELECT COUNT(*)
            FROM (
                SELECT order_id
                FROM stg_orders
                GROUP BY order_id
                HAVING COUNT(*) > 1
            ) AS duplicates;
            """
        ),

        (
            "Null order IDs",
            """
            SELECT COUNT(*)
            FROM stg_orders
            WHERE order_id IS NULL;
            """
        ),

        (
            "Invalid delivery dates",
            """
            SELECT COUNT(*)
            FROM stg_orders
            WHERE order_delivered_customer_date IS NOT NULL
              AND order_delivered_customer_date < order_purchase_timestamp;
            """
        ),

        (
            "Orders without customers",
            """
            SELECT COUNT(*)
            FROM stg_orders o
            LEFT JOIN stg_customers c
                ON o.customer_id = c.customer_id
            WHERE c.customer_id IS NULL;
            """
        ),

        (
            "Negative item values",
            """
            SELECT COUNT(*)
            FROM stg_order_items
            WHERE price < 0
               OR freight_value < 0;
            """
        ),

        (
            "Invalid review scores",
            """
            SELECT COUNT(*)
            FROM stg_order_reviews
            WHERE review_score < 1
               OR review_score > 5;
            """
        ),
    ]

    failed_checks = []

    print("\n========== PRE-MART DATA QUALITY CHECKS ==========\n")

    with engine.connect() as connection:

        for check_name, query in checks:

            result = connection.execute(text(query))
            problematic_rows = result.scalar()

            if problematic_rows == 0:
                print(f"PASS: {check_name}")
            else:
                print(
                    f"FAIL: {check_name} "
                    f"({problematic_rows} problematic rows)"
                )

                failed_checks.append(
                    (check_name, problematic_rows)
                )

    print("\n==================================================\n")

    if failed_checks:

        print("CRITICAL DATA QUALITY CHECKS FAILED:")

        for check_name, problematic_rows in failed_checks:
            print(
                f"- {check_name}: "
                f"{problematic_rows} problematic rows"
            )

        raise RuntimeError(
            "Critical data quality checks failed. "
            "Pipeline stopped before MART creation."
        )

    print("All pre-MART critical checks passed.")


# ============================================================
# POST-MART QUALITY CHECKS
# ============================================================

def run_post_mart_quality_checks():

    engine = get_engine()

    checks = [
        (
            "Duplicate rows in mart",
            """
            SELECT COUNT(*)
            FROM (
                SELECT order_id
                FROM mart_order_summary
                GROUP BY order_id
                HAVING COUNT(*) > 1
            ) AS duplicates;
            """
        )
    ]

    failed_checks = []

    print("\n========== POST-MART DATA QUALITY CHECKS ==========\n")

    with engine.connect() as connection:

        for check_name, query in checks:

            result = connection.execute(text(query))
            problematic_rows = result.scalar()

            if problematic_rows == 0:
                print(f"PASS: {check_name}")
            else:
                print(
                    f"FAIL: {check_name} "
                    f"({problematic_rows} problematic rows)"
                )

                failed_checks.append(
                    (check_name, problematic_rows)
                )

    print("\n===================================================\n")

    if failed_checks:

        print("POST-MART DATA QUALITY CHECKS FAILED:")

        for check_name, problematic_rows in failed_checks:
            print(
                f"- {check_name}: "
                f"{problematic_rows} problematic rows"
            )

        raise RuntimeError(
            "Post-MART data quality checks failed."
        )

    print("All post-MART critical checks passed.")


# ============================================================
# DATA QUALITY WARNINGS
# These are investigated and reported but do NOT stop pipeline.
# ============================================================

def run_quality_warnings():

    engine = get_engine()

    print("\n========== DATA QUALITY WARNINGS ==========\n")

    with engine.connect() as connection:

        # ----------------------------------------------------
        # Multiple reviews
        # ----------------------------------------------------

        result = connection.execute(text("""
            SELECT COUNT(*)
            FROM (
                SELECT order_id
                FROM stg_order_reviews
                GROUP BY order_id
                HAVING COUNT(*) > 1
            ) AS multiple_reviews;
        """))

        multiple_reviews = result.scalar()

        print(
            f"WARNING: Orders with multiple reviews: "
            f"{multiple_reviews}"
        )

        # ----------------------------------------------------
        # Delivered orders with missing delivery date
        # ----------------------------------------------------

        result = connection.execute(text("""
            SELECT COUNT(*)
            FROM stg_orders
            WHERE order_status = 'delivered'
              AND order_delivered_customer_date IS NULL;
        """))

        missing_delivery_dates = result.scalar()

        print(
            f"WARNING: Delivered orders missing delivery date: "
            f"{missing_delivery_dates}"
        )

        # ----------------------------------------------------
        # Payment reconciliation
        # ----------------------------------------------------

        result = connection.execute(text("""
            WITH item_totals AS (
                SELECT
                    order_id,
                    SUM(price + freight_value) AS item_total
                FROM stg_order_items
                GROUP BY order_id
            ),
            payment_totals AS (
                SELECT
                    order_id,
                    SUM(payment_value) AS payment_total
                FROM stg_order_payments
                GROUP BY order_id
            )
            SELECT
                COUNT(*) AS orders_compared,
                COUNT(*) FILTER (
                    WHERE ABS(
                        COALESCE(item_total, 0)
                        - COALESCE(payment_total, 0)
                    ) > 0.01
                ) AS mismatch_rows,
                ROUND(
                    SUM(
                        ABS(
                            COALESCE(item_total, 0)
                            - COALESCE(payment_total, 0)
                        )
                    )::numeric,
                    2
                ) AS total_absolute_difference
            FROM item_totals i
            FULL OUTER JOIN payment_totals p
                ON i.order_id = p.order_id;
        """))

        payment_result = result.fetchone()

        print(
            f"WARNING: Payment reconciliation mismatches: "
            f"{payment_result.mismatch_rows}"
        )

        print(
            f"Total absolute payment difference: "
            f"BRL {payment_result.total_absolute_difference}"
        )

    print("\n==========================================\n")

    print(
        "Data-quality warnings recorded. "
        "Warnings do not stop the pipeline."
    )


# ============================================================
# STANDALONE EXECUTION
# ============================================================

if __name__ == "__main__":

    run_pre_mart_quality_checks()

    run_post_mart_quality_checks()

    run_quality_warnings()