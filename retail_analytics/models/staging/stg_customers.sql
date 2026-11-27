SELECT
    customer_id,
    TRIM(first_name) AS first_name,
    TRIM(last_name) AS last_name,
    NULLIF(LOWER(TRIM(email)), '') AS email,
    NULLIF(TRIM(phone), '') AS phone,
    signup_date,
    is_active,
    created_at,
    updated_at
FROM {{ source('retail_source', 'customers') }}
