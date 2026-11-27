SELECT
    md5(oi.order_item_id::text) AS order_item_key,
    oi.order_item_id,
    oi.order_id,
    c.customer_key,
    p.product_key,
    p.category_key,
    TO_CHAR(o.order_date::date, 'YYYYMMDD')::integer AS order_date_key,

    oi.quantity,
    oi.unit_price,
    COALESCE(oi.discount_pct, 0) AS discount_pct,

    oi.quantity * oi.unit_price AS gross_line_amount,

    oi.quantity * oi.unit_price
        * COALESCE(oi.discount_pct, 0) / 100.0 AS discount_amount,

    oi.quantity * oi.unit_price
        * (1 - COALESCE(oi.discount_pct, 0) / 100.0)
        AS net_line_amount,

    oi.quantity > 0 AS has_valid_quantity,

    oi.created_at,
    oi.updated_at

FROM {{ ref('stg_order_items') }} AS oi

LEFT JOIN {{ ref('stg_orders') }} AS o
    ON oi.order_id = o.order_id

LEFT JOIN {{ ref('dim_customers') }} AS c
    ON o.customer_id = c.customer_id

LEFT JOIN {{ ref('dim_products') }} AS p
    ON oi.product_id = p.product_id