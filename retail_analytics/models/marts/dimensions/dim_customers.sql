SELECT
    md5(customer_id::text) AS customer_key,
    customer_id,
    first_name,
    last_name,
    NULLIF(TRIM(CONCAT(first_name, ' ', last_name)), '') AS full_name,
    email,
    phone,
    signup_date,
    is_active,
    created_at,
    updated_at
FROM {{ ref('stg_customers') }}