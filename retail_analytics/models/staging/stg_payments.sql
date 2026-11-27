SELECT
    payment_id,
    order_id,
    LOWER(TRIM(payment_method)) AS payment_method,
    LOWER(TRIM(payment_status)) AS payment_status,
    amount,
    NULLIF(TRIM(transaction_ref), '') AS transaction_ref,
    paid_at,
    created_at,
    updated_at
FROM {{ source('retail_source', 'payments') }}
