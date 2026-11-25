
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.db_connection import get_database_engine
from sqlalchemy import text


def main():
    engine = get_database_engine("source")

    tables = {
        "categories": "category_id",
        "customers": "customer_id",
        "addresses": "address_id",
        "products": "product_id",
        "orders": "order_id",
        "order_items": "order_item_id",
        "payments": "payment_id"
    }

    relationships = [
        ("addresses", "customer_id", "customers", "customer_id"),
        ("products", "category_id", "categories", "category_id"),
        ("orders", "customer_id", "customers", "customer_id"),
        ("orders", "shipping_address_id", "addresses", "address_id"),
        ("order_items", "order_id", "orders", "order_id"),
        ("order_items", "product_id", "products", "product_id"),
        ("payments", "order_id", "orders", "order_id")
    ]

    columns_to_check = {
        "categories": ["category_name", "description"],
        "customers": ["first_name", "last_name", "email", "phone"],
        "addresses": [
            "customer_id", "address_type", "address_line",
            "city", "state", "country", "postal_code"
        ],
        "products": [
            "category_id", "sku", "product_name",
            "unit_price", "cost_price"
        ],
        "orders": [
            "customer_id", "shipping_address_id",
            "order_date", "status", "total_amount"
        ],
        "order_items": [
            "order_id", "product_id", "quantity",
            "unit_price", "discount_pct"
        ],
        "payments": [
            "order_id", "payment_method", "payment_status",
            "amount", "transaction_ref", "paid_at"
        ]
    }

    try:
        with engine.connect() as connection:

            # TEST 1: PRIMARY ID DUPLICATE CHECK
            print("\nPRIMARY ID DUPLICATE CHECK")
            print("=" * 65)

            for table, column in tables.items():
                query = text(f"""
                    SELECT
                        COUNT(*) AS total_rows,
                        COUNT(DISTINCT {column}) AS unique_ids,
                        COUNT(*) - COUNT(DISTINCT {column}) AS duplicate_ids
                    FROM shop.{table};
                """)

                result = connection.execute(query).fetchone()

                print(f"\nTable: {table}")
                print(f"Total rows: {result.total_rows}")
                print(f"Unique IDs: {result.unique_ids}")
                print(f"Duplicate IDs: {result.duplicate_ids}")

            # TEST 2: DATABASE RELATIONSHIP CHECK
            print("\n\nDATABASE RELATIONSHIP CHECK")
            print("=" * 65)

            for child_table, child_column, parent_table, parent_column in relationships:
                query = text(f"""
                    SELECT COUNT(*)
                    FROM shop.{child_table} child
                    LEFT JOIN shop.{parent_table} parent
                        ON child.{child_column} = parent.{parent_column}
                    WHERE child.{child_column} IS NOT NULL
                      AND parent.{parent_column} IS NULL;
                """)

                orphan_count = connection.execute(query).scalar()

                print(
                    f"\n{child_table}.{child_column} -> "
                    f"{parent_table}.{parent_column}"
                )
                print(f"Orphan records: {orphan_count}")

            # TEST 3: MISSING VALUES CHECK
            print("\n\nMISSING VALUES CHECK")
            print("=" * 65)

            for table, columns in columns_to_check.items():
                print(f"\nTable: {table}")

                for column in columns:
                    query = text(f"""
                        SELECT COUNT(*)
                        FROM shop.{table}
                        WHERE {column} IS NULL;
                    """)

                    missing_count = connection.execute(query).scalar()
                    print(f"{column}: {missing_count} missing values")

            # TEST 4: PAYMENT STATUS INVESTIGATION
            print("\n\nPAYMENT STATUS INVESTIGATION")
            print("=" * 65)

            print("\nPAYMENT COUNTS BY STATUS")

            query = text("""
                SELECT payment_status, COUNT(*) AS total_payments
                FROM shop.payments
                GROUP BY payment_status
                ORDER BY total_payments DESC;
            """)

            for row in connection.execute(query).fetchall():
                print(f"{row.payment_status}: {row.total_payments}")

            print("\nMISSING PAYMENT DATES BY STATUS")

            query = text("""
                SELECT
                    payment_status,
                    COUNT(*) AS total_payments,
                    COUNT(*) FILTER (WHERE paid_at IS NULL) AS missing_dates,
                    COUNT(*) FILTER (WHERE paid_at IS NOT NULL) AS available_dates
                FROM shop.payments
                GROUP BY payment_status
                ORDER BY payment_status;
            """)

            for row in connection.execute(query).fetchall():
                print(f"\nStatus: {row.payment_status}")
                print(f"Total payments: {row.total_payments}")
                print(f"Missing payment dates: {row.missing_dates}")
                print(f"Available payment dates: {row.available_dates}")

            print("\nSUCCESSFUL PAYMENTS WITHOUT PAID_AT")

            query = text("""
                SELECT COUNT(*)
                FROM shop.payments
                WHERE LOWER(TRIM(payment_status)) = 'successful'
                  AND paid_at IS NULL;
            """)

            result = connection.execute(query).scalar()
            print(f"Successful payments missing dates: {result}")

            # TEST 5: BUSINESS VALUE VALIDATION
            print("\n\nBUSINESS VALUE VALIDATION")
            print("=" * 65)

            checks = {
                "Products with zero or negative selling price": """
                    SELECT COUNT(*) FROM shop.products
                    WHERE unit_price <= 0;
                """,
                "Products with negative cost price": """
                    SELECT COUNT(*) FROM shop.products
                    WHERE cost_price < 0;
                """,
                "Orders with negative total amount": """
                    SELECT COUNT(*) FROM shop.orders
                    WHERE total_amount < 0;
                """,
                "Order items with zero or negative quantity": """
                    SELECT COUNT(*) FROM shop.order_items
                    WHERE quantity <= 0;
                """,
                "Order items with zero or negative unit price": """
                    SELECT COUNT(*) FROM shop.order_items
                    WHERE unit_price <= 0;
                """,
                "Order items with discounts below 0 percent": """
                    SELECT COUNT(*) FROM shop.order_items
                    WHERE discount_pct < 0;
                """,
                "Order items with discounts above 100 percent": """
                    SELECT COUNT(*) FROM shop.order_items
                    WHERE discount_pct > 100;
                """,
                "Payments with zero or negative amounts": """
                    SELECT COUNT(*) FROM shop.payments
                    WHERE amount <= 0;
                """
            }

            for description, sql_query in checks.items():
                result = connection.execute(text(sql_query)).scalar()
                print(f"\n{description}")
                print(f"Invalid records: {result}")

            # TEST 6: DISTINCT BUSINESS VALUES
            print("\n\nDISTINCT BUSINESS VALUES")
            print("=" * 65)

            value_queries = {
                "ORDER STATUSES": """
                    SELECT DISTINCT status FROM shop.orders ORDER BY status;
                """,
                "PAYMENT METHODS": """
                    SELECT DISTINCT payment_method FROM shop.payments
                    ORDER BY payment_method;
                """,
                "PAYMENT STATUSES": """
                    SELECT DISTINCT payment_status FROM shop.payments
                    ORDER BY payment_status;
                """,
                "ADDRESS TYPES": """
                    SELECT DISTINCT address_type FROM shop.addresses
                    ORDER BY address_type;
                """
            }

            for heading, sql_query in value_queries.items():
                print(f"\n{heading}")

                for row in connection.execute(text(sql_query)).fetchall():
                    print(row[0])

            # TEST 7: INVALID BUSINESS RECORD INVESTIGATION
            print("\n\nINVALID BUSINESS RECORD INVESTIGATION")
            print("=" * 65)

            print("\nORDERS WITH NEGATIVE TOTAL AMOUNTS")

            query = text("""
                SELECT order_id, customer_id, order_date, status, total_amount
                FROM shop.orders
                WHERE total_amount < 0;
            """)

            for row in connection.execute(query).fetchall():
                print(row)

            print("\nORDER ITEMS WITH ZERO OR NEGATIVE QUANTITIES")

            query = text("""
                SELECT
                    oi.order_item_id,
                    oi.order_id,
                    o.status AS order_status,
                    oi.product_id,
                    p.product_name,
                    oi.quantity,
                    oi.unit_price
                FROM shop.order_items oi
                JOIN shop.orders o ON oi.order_id = o.order_id
                JOIN shop.products p ON oi.product_id = p.product_id
                WHERE oi.quantity <= 0
                ORDER BY oi.order_id;
            """)

            for row in connection.execute(query).fetchall():
                print(row)

            print("\nORDER STATUS COUNTS")

            query = text("""
                SELECT
                    status,
                    LOWER(TRIM(status)) AS normalized_status,
                    COUNT(*) AS total_orders
                FROM shop.orders
                GROUP BY status, LOWER(TRIM(status))
                ORDER BY normalized_status, status;
            """)

            for row in connection.execute(query).fetchall():
                print(row)

            # TEST 8: AFFECTED ORDER INVESTIGATION
            print("\n\nAFFECTED ORDER INVESTIGATION")
            print("=" * 65)

            print("\nALL ORDER ITEMS FOR AFFECTED ORDERS")

            query = text("""
                SELECT
                    o.order_id,
                    o.customer_id,
                    o.status,
                    o.total_amount,
                    oi.order_item_id,
                    p.product_name,
                    oi.quantity,
                    oi.unit_price,
                    oi.discount_pct,
                    (
                        oi.quantity * oi.unit_price *
                        (1 - oi.discount_pct / 100)
                    ) AS calculated_line_total
                FROM shop.orders o
                JOIN shop.order_items oi ON o.order_id = oi.order_id
                JOIN shop.products p ON oi.product_id = p.product_id
                WHERE o.order_id IN (300, 600, 900, 1200, 1500)
                ORDER BY o.order_id, oi.order_item_id;
            """)

            for row in connection.execute(query).fetchall():
                print(row)

            print("\nPAYMENTS FOR AFFECTED ORDERS")

            query = text("""
                SELECT
                    o.order_id,
                    o.status AS order_status,
                    o.total_amount,
                    p.payment_id,
                    p.payment_method,
                    p.payment_status,
                    p.amount,
                    p.transaction_ref,
                    p.paid_at
                FROM shop.orders o
                LEFT JOIN shop.payments p ON o.order_id = p.order_id
                WHERE o.order_id IN (300, 600, 900, 1200, 1500)
                ORDER BY o.order_id, p.payment_id;
            """)

            for row in connection.execute(query).fetchall():
                print(row)

            # TEST 9: ORDER TOTAL RECONCILIATION
            print("\n\nORDER TOTAL RECONCILIATION")
            print("=" * 65)

            query = text("""
                WITH item_totals AS (
                    SELECT
                        order_id,
                        SUM(
                            quantity * unit_price *
                            (1 - discount_pct / 100)
                        ) AS calculated_item_total,
                        COUNT(*) AS item_count
                    FROM shop.order_items
                    GROUP BY order_id
                )
                SELECT
                    o.order_id,
                    o.status,
                    o.total_amount AS recorded_total,
                    COALESCE(i.calculated_item_total, 0)
                        AS calculated_item_total,
                    o.total_amount -
                        COALESCE(i.calculated_item_total, 0)
                        AS difference,
                    COALESCE(i.item_count, 0) AS item_count
                FROM shop.orders o
                LEFT JOIN item_totals i ON o.order_id = i.order_id
                WHERE ABS(
                    o.total_amount -
                    COALESCE(i.calculated_item_total, 0)
                ) > 0.01
                ORDER BY o.order_id;
            """)

            results = connection.execute(query).fetchall()

            print(f"\nOrders with total discrepancies: {len(results)}")

            for row in results:
                print(row)

            print("\nRECONCILIATION SUMMARY")

            query = text("""
                WITH item_totals AS (
                    SELECT
                        order_id,
                        SUM(
                            quantity * unit_price *
                            (1 - discount_pct / 100)
                        ) AS calculated_item_total
                    FROM shop.order_items
                    GROUP BY order_id
                )
                SELECT
                    COUNT(*) AS total_orders,
                    COUNT(*) FILTER (
                        WHERE ABS(
                            o.total_amount -
                            COALESCE(i.calculated_item_total, 0)
                        ) <= 0.01
                    ) AS matching_orders,
                    COUNT(*) FILTER (
                        WHERE ABS(
                            o.total_amount -
                            COALESCE(i.calculated_item_total, 0)
                        ) > 0.01
                    ) AS mismatching_orders
                FROM shop.orders o
                LEFT JOIN item_totals i ON o.order_id = i.order_id;
            """)

            result = connection.execute(query).fetchone()

            print(f"Total orders: {result.total_orders}")
            print(f"Matching orders: {result.matching_orders}")
            print(f"Mismatching orders: {result.mismatching_orders}")

            # TEST 10: INVESTIGATE THE FIXED 1,500 DIFFERENCE
            print("\n\nFIXED ORDER DIFFERENCE INVESTIGATION")
            print("=" * 65)

            query = text("""
                WITH item_totals AS (
                    SELECT
                        order_id,
                        SUM(
                            quantity * unit_price *
                            (1 - discount_pct / 100)
                        ) AS calculated_item_total
                    FROM shop.order_items
                    GROUP BY order_id
                ),
                payment_totals AS (
                    SELECT
                        order_id,
                        COUNT(*) AS payment_attempts,
                        COUNT(*) FILTER (
                            WHERE LOWER(TRIM(payment_status)) = 'successful'
                        ) AS successful_attempts,
                        SUM(amount) FILTER (
                            WHERE LOWER(TRIM(payment_status)) = 'successful'
                        ) AS successful_payment_total
                    FROM shop.payments
                    GROUP BY order_id
                )
                SELECT
                    o.order_id,
                    o.status,
                    o.total_amount,
                    i.calculated_item_total,
                    o.total_amount - i.calculated_item_total AS difference,
                    o.shipping_address_id,
                    a.city,
                    a.state,
                    a.country,
                    COALESCE(p.payment_attempts, 0) AS payment_attempts,
                    COALESCE(p.successful_attempts, 0) AS successful_attempts,
                    p.successful_payment_total
                FROM shop.orders o
                JOIN item_totals i ON o.order_id = i.order_id
                LEFT JOIN shop.addresses a
                    ON o.shipping_address_id = a.address_id
                LEFT JOIN payment_totals p ON o.order_id = p.order_id
                WHERE o.order_id IN (200, 400, 600, 800, 1000, 1200, 1400)
                ORDER BY o.order_id;
            """)

            results = connection.execute(query).fetchall()

            print("\nSEVEN ORDERS WITH A 1,500 DIFFERENCE")

            for row in results:
                print(row)

            print("\nINVESTIGATION COMPLETE")

    except Exception as error:
        print("\nDATABASE TEST FAILED")
        print(f"Error: {error}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
