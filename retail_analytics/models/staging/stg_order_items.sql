SELECT
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    discount_pct,
    created_at,
    updated_at
FROM {{ source('retail_source', 'order_items') }}
