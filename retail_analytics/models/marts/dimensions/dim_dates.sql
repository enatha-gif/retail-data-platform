WITH all_dates AS (
    SELECT order_date::date AS event_date
    FROM {{ ref('stg_orders') }}

    UNION ALL

    SELECT signup_date AS event_date
    FROM {{ ref('stg_customers') }}
    WHERE signup_date IS NOT NULL
),

date_bounds AS (
    SELECT
        MIN(event_date) AS min_date,
        MAX(event_date) AS max_date
    FROM all_dates
),

calendar AS (
    SELECT generate_series(
        min_date::timestamp,
        max_date::timestamp,
        INTERVAL '1 day'
    )::date AS calendar_date
    FROM date_bounds
    WHERE min_date IS NOT NULL
)

SELECT
    TO_CHAR(calendar_date, 'YYYYMMDD')::integer AS date_key,
    calendar_date,
    EXTRACT(DAY FROM calendar_date)::integer AS day_number,
    EXTRACT(MONTH FROM calendar_date)::integer AS month_number,
    TRIM(TO_CHAR(calendar_date, 'Month')) AS month_name,
    EXTRACT(QUARTER FROM calendar_date)::integer AS quarter_number,
    EXTRACT(YEAR FROM calendar_date)::integer AS year_number,
    EXTRACT(ISODOW FROM calendar_date)::integer AS day_of_week,
    TRIM(TO_CHAR(calendar_date, 'Day')) AS day_name,
    EXTRACT(ISODOW FROM calendar_date) IN (6, 7) AS is_weekend
FROM calendar