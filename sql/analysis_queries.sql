
-- ============================================================
-- ONLINE RETAIL DATA PLATFORM
-- BUSINESS ANALYSIS QUERIES
-- Database: retail_dw
-- Schema: analytics
-- ============================================================


-- ============================================================
-- QUERY 1: MONTHLY REVENUE VS PREVIOUS MONTH
-- Business question:
-- How does monthly revenue compare with the previous month?
-- SQL concepts: CTE, SUM(), LAG()
-- ============================================================

WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::date AS sales_month,
        SUM(oi.net_line_amount) AS monthly_revenue
    FROM analytics.fct_order_items AS oi
    INNER JOIN analytics.fct_orders AS o
        ON oi.order_id = o.order_id
    WHERE o.order_status = 'completed'
  AND o.order_date <= CURRENT_TIMESTAMP
    GROUP BY DATE_TRUNC('month', o.order_date)::date
),

revenue_comparison AS (
    SELECT
        sales_month,
        monthly_revenue,
        LAG(monthly_revenue) OVER (
            ORDER BY sales_month
        ) AS previous_month_revenue
    FROM monthly_revenue
)

SELECT
    sales_month,
    ROUND(monthly_revenue, 2) AS monthly_revenue,
    ROUND(previous_month_revenue, 2) AS previous_month_revenue,
    ROUND(
        monthly_revenue - previous_month_revenue,
        2
    ) AS revenue_difference,
    ROUND(
        100.0 * (monthly_revenue - previous_month_revenue)
        / NULLIF(previous_month_revenue, 0),
        2
    ) AS percentage_change
FROM revenue_comparison
ORDER BY sales_month;


-- ============================================================
-- QUERY 2: TOP FIVE PRODUCTS PER CATEGORY
-- Business question:
-- Which five products generate the highest revenue in each
-- product category?
-- SQL concepts: JOIN, GROUP BY, ROW_NUMBER()
-- ============================================================

WITH product_revenue AS (
    SELECT
        p.category_name,
        p.product_id,
        p.product_name,
        SUM(oi.net_line_amount) AS total_revenue
    FROM analytics.fct_order_items AS oi
    INNER JOIN analytics.fct_orders AS o
        ON oi.order_id = o.order_id
    INNER JOIN analytics.dim_products AS p
        ON oi.product_key = p.product_key
    WHERE o.order_status = 'completed'
  AND o.order_date <= CURRENT_TIMESTAMP
    GROUP BY
        p.category_name,
        p.product_id,
        p.product_name
),

ranked_products AS (
    SELECT
        category_name,
        product_id,
        product_name,
        total_revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_name
            ORDER BY total_revenue DESC
        ) AS product_rank
    FROM product_revenue
)

SELECT
    category_name,
    product_id,
    product_name,
    ROUND(total_revenue, 2) AS total_revenue,
    product_rank
FROM ranked_products
WHERE product_rank <= 5
ORDER BY category_name, product_rank;


-- ============================================================
-- QUERY 3: CUSTOMER LIFETIME VALUE (LTV)
-- Business question:
-- Which customers generate the highest lifetime revenue?
-- SQL concepts: JOIN, SUM(), COUNT(), CASE
-- ============================================================

WITH customer_value AS (
    SELECT
        c.customer_id,
        c.full_name,
        c.email,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.net_line_amount) AS lifetime_value
    FROM analytics.dim_customers AS c
    INNER JOIN analytics.fct_orders AS o
        ON c.customer_key = o.customer_key
    INNER JOIN analytics.fct_order_items AS oi
        ON o.order_id = oi.order_id
   WHERE o.order_status = 'completed'
  AND o.order_date <= CURRENT_TIMESTAMP
    GROUP BY
        c.customer_id,
        c.full_name,
        c.email
)

SELECT
    customer_id,
    full_name,
    total_orders,
    ROUND(lifetime_value, 2) AS lifetime_value,
    CASE
        WHEN lifetime_value >= 1000000 THEN 'High Value'
        WHEN lifetime_value >= 500000 THEN 'Medium Value'
        ELSE 'Low Value'
    END AS customer_segment
FROM customer_value
ORDER BY lifetime_value DESC;


-- ============================================================
-- QUERY 4: PAYMENT SUCCESS RATE BY PAYMENT METHOD
-- Business question:
-- Which payment methods have the highest success rate?
-- SQL concepts: Conditional aggregation, CASE
-- ============================================================

SELECT
    payment_method,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (
        WHERE payment_status = 'successful'
    ) AS successful_transactions,
    COUNT(*) FILTER (
        WHERE payment_status = 'failed'
    ) AS failed_transactions,
    COUNT(*) FILTER (
    WHERE payment_status = 'pending'
) AS pending_transactions,

COUNT(*) FILTER (
    WHERE payment_status = 'refunded'
) AS refunded_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE payment_status = 'successful'
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS success_rate_percentage
FROM analytics.fct_payments
GROUP BY payment_method
ORDER BY success_rate_percentage DESC;


-- ============================================================
-- QUERY 5: NEW VS RETURNING CUSTOMERS BY MONTH
-- Business question:
-- How many new and returning customers do we have each month?
-- SQL concepts: CTE, MIN(), COUNT(DISTINCT)
-- ============================================================

-- ============================================================
-- QUERY 5: NEW VS RETURNING CUSTOMERS BY MONTH
-- Business question:
-- How many new and returning customers do we have each month?
-- SQL concepts: CTE, MIN(), COUNT(DISTINCT)
-- ============================================================

WITH first_customer_order AS (
    SELECT
        customer_key,
        MIN(order_date::date) AS first_order_date
    FROM analytics.fct_orders
    WHERE order_status = 'completed'
      AND order_date <= CURRENT_TIMESTAMP
    GROUP BY customer_key
),

monthly_customer_activity AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::date AS activity_month,
        o.customer_key,
        f.first_order_date
    FROM analytics.fct_orders AS o
    INNER JOIN first_customer_order AS f
        ON o.customer_key = f.customer_key
    WHERE o.order_status = 'completed'
      AND o.order_date <= CURRENT_TIMESTAMP
)

SELECT
    activity_month,
    COUNT(DISTINCT customer_key) FILTER (
        WHERE DATE_TRUNC('month', first_order_date)::date = activity_month
    ) AS new_customers,
    COUNT(DISTINCT customer_key) FILTER (
        WHERE DATE_TRUNC('month', first_order_date)::date < activity_month
    ) AS returning_customers,
    COUNT(DISTINCT customer_key) AS total_active_customers
FROM monthly_customer_activity
GROUP BY activity_month
ORDER BY activity_month;
