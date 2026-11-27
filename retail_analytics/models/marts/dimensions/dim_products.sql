SELECT
    md5(p.product_id::text) AS product_key,
    p.product_id,
    p.sku,
    p.product_name,
    p.category_id,
    c.category_key,
    c.category_name,
    p.unit_price,
    p.cost_price,
    p.is_active,
    p.created_at,
    p.updated_at
FROM {{ ref('stg_products') }} AS p
LEFT JOIN {{ ref('dim_categories') }} AS c
    ON p.category_id = c.category_id