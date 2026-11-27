SELECT
    md5(category_id::text) AS category_key,
    category_id,
    category_name,
    description,
    created_at,
    updated_at
FROM {{ ref('stg_categories') }}