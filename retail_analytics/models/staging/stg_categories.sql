SELECT
    category_id,
    TRIM(category_name) AS category_name,
    description,
    created_at,
    updated_at
FROM {{ source('retail_source', 'categories') }}
