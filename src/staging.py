from sqlalchemy import text

from database import get_engine


def build_staging_tables():

    engine = get_engine()

    with engine.begin() as connection:

        print("Building stg_orders...")

        connection.execute(text("""
            DROP TABLE IF EXISTS stg_orders;

            CREATE TABLE stg_orders AS
            SELECT
                TRIM(order_id) AS order_id,
                TRIM(customer_id) AS customer_id,
                TRIM(order_status) AS order_status,

                NULLIF(TRIM(order_purchase_timestamp), '')::timestamp
                    AS order_purchase_timestamp,

                NULLIF(TRIM(order_approved_at), '')::timestamp
                    AS order_approved_at,

                NULLIF(TRIM(order_delivered_carrier_date), '')::timestamp
                    AS order_delivered_carrier_date,

                NULLIF(TRIM(order_delivered_customer_date), '')::timestamp
                    AS order_delivered_customer_date,

                NULLIF(TRIM(order_estimated_delivery_date), '')::timestamp
                    AS order_estimated_delivery_date

            FROM raw_orders;
        """))

        print("stg_orders created.")

        print("Building stg_customers...")

        connection.execute(text("""
            DROP TABLE IF EXISTS stg_customers;

            CREATE TABLE stg_customers AS
            SELECT
                TRIM(customer_id) AS customer_id,
                TRIM(customer_unique_id) AS customer_unique_id,
                customer_zip_code_prefix::integer
                    AS customer_zip_code_prefix,
                TRIM(customer_city) AS customer_city,
                TRIM(customer_state) AS customer_state

            FROM raw_customers;
        """))

        print("stg_customers created.")

        print("Building stg_order_items...")

        connection.execute(text("""
            DROP TABLE IF EXISTS stg_order_items;

            CREATE TABLE stg_order_items AS
            SELECT
                TRIM(order_id) AS order_id,
                order_item_id::integer AS order_item_id,
                TRIM(product_id) AS product_id,
                TRIM(seller_id) AS seller_id,

                NULLIF(TRIM(shipping_limit_date), '')::timestamp
                    AS shipping_limit_date,

                price::numeric(12,2) AS price,
                freight_value::numeric(12,2) AS freight_value

            FROM raw_order_items;
        """))

        print("stg_order_items created.")

        print("Building stg_order_payments...")

        connection.execute(text("""
            DROP TABLE IF EXISTS stg_order_payments;

            CREATE TABLE stg_order_payments AS
            SELECT
                TRIM(order_id) AS order_id,
                payment_sequential::integer AS payment_sequential,
                TRIM(payment_type) AS payment_type,
                payment_installments::integer AS payment_installments,
                payment_value::numeric(12,2) AS payment_value

            FROM raw_order_payments;
        """))

        print("stg_order_payments created.")

        print("Building stg_order_reviews...")

        connection.execute(text("""
            DROP TABLE IF EXISTS stg_order_reviews;

            CREATE TABLE stg_order_reviews AS
            SELECT
                TRIM(review_id) AS review_id,
                TRIM(order_id) AS order_id,
                review_score::integer AS review_score,
                NULLIF(TRIM(review_comment_title), '') AS review_comment_title,
                NULLIF(TRIM(review_comment_message), '') AS review_comment_message,

                NULLIF(TRIM(review_creation_date), '')::timestamp
                    AS review_creation_date,

                NULLIF(TRIM(review_answer_timestamp), '')::timestamp
                    AS review_answer_timestamp

            FROM raw_order_reviews;
        """))

        print("stg_order_reviews created.")

        print("Building stg_products...")

        connection.execute(text("""
            DROP TABLE IF EXISTS stg_products;

            CREATE TABLE stg_products AS
            SELECT
                TRIM(product_id) AS product_id,
                NULLIF(TRIM(product_category_name), '') 
                    AS product_category_name,

                product_name_lenght::integer AS product_name_length,
                product_description_lenght::integer
                    AS product_description_length,

                product_photos_qty::integer AS product_photos_qty,
                product_weight_g::numeric AS product_weight_g,
                product_length_cm::numeric AS product_length_cm,
                product_height_cm::numeric AS product_height_cm,
                product_width_cm::numeric AS product_width_cm

            FROM raw_products;
        """))

        print("stg_products created.")

        print("Building stg_sellers...")

        connection.execute(text("""
            DROP TABLE IF EXISTS stg_sellers;

            CREATE TABLE stg_sellers AS
            SELECT
                TRIM(seller_id) AS seller_id,
                seller_zip_code_prefix::integer
                    AS seller_zip_code_prefix,
                TRIM(seller_city) AS seller_city,
                TRIM(seller_state) AS seller_state

            FROM raw_sellers;
        """))

        print("stg_sellers created.")

        print("Building stg_category_translation...")

        connection.execute(text("""
            DROP TABLE IF EXISTS stg_category_translation;

            CREATE TABLE stg_category_translation AS
            SELECT
                TRIM(product_category_name) AS product_category_name,
                TRIM(product_category_name_english)
                    AS product_category_name_english

            FROM raw_category_translation;
        """))

        print("stg_category_translation created.")

        print("Building stg_geolocation...")

        connection.execute(text("""
    DROP TABLE IF EXISTS stg_geolocation;

    CREATE TABLE stg_geolocation AS
    SELECT
        geolocation_zip_code_prefix::integer
            AS geolocation_zip_code_prefix,

        geolocation_lat::numeric AS geolocation_lat,
        geolocation_lng::numeric AS geolocation_lng,

        TRIM(geolocation_city) AS geolocation_city,
        TRIM(geolocation_state) AS geolocation_state

    FROM raw_geolocation;
"""))

        print("stg_geolocation created.")

    print("All staging tables created successfully.")


if __name__ == "__main__":
    build_staging_tables()