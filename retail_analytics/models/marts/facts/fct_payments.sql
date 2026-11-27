SELECT
    md5(p.payment_id::text) AS payment_key,
    p.payment_id,
    p.order_id,
    c.customer_key,
    TO_CHAR(o.order_date::date, 'YYYYMMDD')::integer AS order_date_key,

    LOWER(TRIM(p.payment_method)) AS payment_method,
    LOWER(TRIM(p.payment_status)) AS payment_status,

    p.amount,
    p.transaction_ref,
    p.paid_at,

    p.payment_status = 'successful' AS is_successful,

    p.created_at,
    p.updated_at

FROM {{ ref('stg_payments') }} AS p

LEFT JOIN {{ ref('stg_orders') }} AS o
    ON p.order_id = o.order_id

LEFT JOIN {{ ref('dim_customers') }} AS c
    ON o.customer_id = c.customer_id