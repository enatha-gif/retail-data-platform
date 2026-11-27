SELECT
    order_id,
    customer_id,
    shipping_address_id,
    order_date,
    CASE
        WHEN LOWER(TRIM(status)) = 'complete' THEN 'completed'
        ELSE LOWER(TRIM(status))
    END AS status,
    total_amount,
    created_at,
    updated_at
FROM {{ source('retail_source', 'orders') }}
