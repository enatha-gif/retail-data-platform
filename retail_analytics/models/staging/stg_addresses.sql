SELECT
    address_id,
    customer_id,
    LOWER(TRIM(address_type)) AS address_type,
    TRIM(address_line) AS address_line,
    TRIM(city) AS city,
    TRIM(state) AS state,
    TRIM(country) AS country,
    NULLIF(TRIM(postal_code), '') AS postal_code,
    is_default,
    created_at,
    updated_at
FROM {{ source('retail_source', 'addresses') }}
