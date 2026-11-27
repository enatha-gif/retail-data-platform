{{
    config(
        materialized='incremental',
        unique_key='order_id',
        incremental_strategy='delete+insert'
    )
}}

SELECT
    md5(o.order_id::text) AS order_key,
    o.order_id,
    c.customer_key,
    TO_CHAR(o.order_date::date, 'YYYYMMDD')::integer AS order_date_key,
    o.shipping_address_id,
    o.status AS order_status,
    o.total_amount,
    o.order_date,
    o.created_at,
    o.updated_at

FROM {{ ref('stg_orders') }} AS o

LEFT JOIN {{ ref('dim_customers') }} AS c
    ON o.customer_id = c.customer_id

{% if is_incremental() %}
WHERE o.updated_at >= (
    SELECT COALESCE(
        MAX(updated_at),
        '1900-01-01'::timestamptz
    )
    FROM {{ this }}
)
{% endif %}