SELECT
    product_id,
    category_id,
    TRIM(sku) AS sku,
    TRIM(product_name) AS product_name,
    unit_price,
    cost_price,
    is_active,
    created_at,
    updated_at
FROM {{ source('retail_source', 'products') }}
