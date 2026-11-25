CREATE SCHEMA IF NOT EXISTS etl_metadata;

CREATE TABLE IF NOT EXISTS etl_metadata.etl_watermarks (
    table_name TEXT PRIMARY KEY,
    last_updated_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    rows_loaded BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS etl_metadata.etl_run_log (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    table_name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    rows_extracted BIGINT DEFAULT 0,
    rows_loaded BIGINT DEFAULT 0,
    error_message TEXT
);
