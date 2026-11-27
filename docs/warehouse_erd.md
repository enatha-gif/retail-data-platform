# Retail Data Warehouse Entity Relationship Diagram

## 1. Overview

The retail data warehouse uses a layered architecture consisting of a PostgreSQL staging layer and a dbt analytical layer.

The staging layer stores data extracted from the source PostgreSQL `shop` schema. The analytical layer transforms the staged data into a dimensional model designed for reporting and business analysis.

The warehouse contains:

- 7 staging tables.
- 4 analytical dimension tables.
- 3 analytical fact tables.

The analytical models are stored in the PostgreSQL `analytics` schema.

## 2. Warehouse Architecture

```mermaid

    A["Source PostgreSQL Database<br/>shop schema"] --> B["Python ETL Pipeline"]
    B --> C["Staging Schema<br/>7 staging tables"]
    C --> D["dbt Transformation Layer"]
    D --> E["Analytics Schema<br/>4 dimensions"]
    D --> F["Analytics Schema<br/>3 fact tables"]
    E --> G["Business Analysis and Reporting"]
    F --> G
```

## 3. Staging Layer

The staging layer contains seven tables extracted from the source database.

| Table | Primary Key | Important Relationships |
|---|---|---|
| staging.categories | category_id | Referenced by products |
| staging.customers | customer_id | Referenced by addresses and orders |
| staging.addresses | address_id | Referenced by orders |
| staging.products | product_id | References categories |
| staging.orders | order_id | References customers and addresses |
| staging.order_items | order_item_id | References orders and products |
| staging.payments | payment_id | References orders |

### Staging Relationships

```mermaid

    CATEGORIES ||--o{ PRODUCTS : contains
    CUSTOMERS ||--o{ ADDRESSES : has
    CUSTOMERS ||--o{ ORDERS : places
    ADDRESSES o|--o{ ORDERS : ships_to
    ORDERS ||--o{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : included_in
    ORDERS ||--o{ PAYMENTS : receives

    CATEGORIES {
        int category_id PK
        text category_name
        text description
    }

    CUSTOMERS {
        bigint customer_id PK
        text first_name
        text last_name
        text email
        text phone
        date signup_date
        boolean is_active
    }

    ADDRESSES {
        bigint address_id PK
        bigint customer_id FK
        text address_type
        text city
        text country
        boolean is_default
    }

    PRODUCTS {
        bigint product_id PK
        int category_id FK
        text sku
        text product_name
        numeric unit_price
        numeric cost_price
    }

    ORDERS {
        bigint order_id PK
        bigint customer_id FK
        bigint shipping_address_id FK
        timestamptz order_date
        text status
        numeric total_amount
    }

    ORDER_ITEMS {
        bigint order_item_id PK
        bigint order_id FK
        bigint product_id FK
        int quantity
        numeric unit_price
        numeric discount_pct
    }

    PAYMENTS {
        bigint payment_id PK
        bigint order_id FK
        text payment_method
        text payment_status
        numeric amount
        timestamptz paid_at
    }
```

## 4. Analytical Dimension Tables

The dbt transformation layer creates four dimensions.

| Dimension | Surrogate Key | Source Identifier | Purpose |
|---|---|---|---|
| dim_customers | customer_key | customer_id | Customer analysis |
| dim_products | product_key | product_id | Product analysis |
| dim_categories | category_key | category_id | Category analysis |
| dim_dates | date_key | calendar_date | Calendar and time analysis |

Surrogate keys are generated using PostgreSQL MD5 hashing for customer, product and category identifiers.

The date dimension uses an integer key in `YYYYMMDD` format.

### Dimension Details

**dim_customers**
- customer_key
- customer_id
- first_name
- last_name
- full_name
- email
- phone
- signup_date
- is_active
- created_at
- updated_at

**dim_products**
- product_key
- product_id
- sku
- product_name
- category_id
- category_key
- category_name
- unit_price
- cost_price
- is_active

**dim_categories**
- category_key
- category_id
- category_name
- description

**dim_dates**
- date_key
- calendar_date
- day_number
- month_number
- month_name
- quarter_number
- year_number
- day_of_week
- day_name
- is_weekend

## 5. Analytical Fact Tables

Three fact tables support business analysis.

| Fact Table | Primary/Unique Identifier | Main Measures |
|---|---|---|
| fct_orders | order_key / order_id | total_amount |
| fct_order_items | order_item_key | quantity, gross_line_amount, discount_amount, net_line_amount |
| fct_payments | payment_key | amount, is_successful |

### Fact Table Relationships

- `fct_orders.customer_key` references `dim_customers.customer_key`.
- `fct_orders.order_date_key` references `dim_dates.date_key`.
- `fct_order_items.customer_key` references `dim_customers.customer_key`.
- `fct_order_items.product_key` references `dim_products.product_key`.
- `fct_order_items.category_key` references the category associated with the product in `dim_products`.
- `fct_order_items.order_date_key` references `dim_dates.date_key`.
- `fct_payments.customer_key` references `dim_customers.customer_key`.
- `fct_payments.order_date_key` references `dim_dates.date_key`.

The fact tables retain original source identifiers such as `order_id`, `payment_id` and `order_item_id` for traceability.

### Analytical Star Schema

```mermaid

    DIM_CUSTOMERS ||--o{ FCT_ORDERS : customer
    DIM_DATES ||--o{ FCT_ORDERS : order_date

    DIM_CUSTOMERS ||--o{ FCT_ORDER_ITEMS : customer
    DIM_PRODUCTS ||--o{ FCT_ORDER_ITEMS : product
    DIM_DATES ||--o{ FCT_ORDER_ITEMS : order_date
    DIM_CATEGORIES ||--o{ FCT_ORDER_ITEMS : category
    
    DIM_CUSTOMERS ||--o{ FCT_PAYMENTS : customer
    DIM_DATES ||--o{ FCT_PAYMENTS : order_date

    DIM_CATEGORIES ||--o{ DIM_PRODUCTS : category

    DIM_CUSTOMERS {
        text customer_key PK
        bigint customer_id
        text full_name
        date signup_date
        boolean is_active
    }

    DIM_PRODUCTS {
        text product_key PK
        bigint product_id
        text sku
        text product_name
        text category_key FK
        numeric unit_price
        numeric cost_price
    }

    DIM_CATEGORIES {
        text category_key PK
        int category_id
        text category_name
    }

    DIM_DATES {
        int date_key PK
        date calendar_date
        int month_number
        int quarter_number
        int year_number
        boolean is_weekend
    }

    FCT_ORDERS {
        text order_key PK
        bigint order_id
        text customer_key FK
        int order_date_key FK
        numeric total_amount
        text order_status
    }

    FCT_ORDER_ITEMS {
        text order_item_key PK
        bigint order_item_id
        bigint order_id
        text customer_key FK
        text product_key FK
        text category_key FK
        int order_date_key FK
        int quantity
        numeric gross_line_amount
        numeric discount_amount
        numeric net_line_amount
    }

    FCT_PAYMENTS {
        text payment_key PK
        bigint payment_id
        bigint order_id
        text customer_key FK
        int order_date_key FK
        text payment_method
        text payment_status
        numeric amount
        boolean is_successful
    }
```

## 6. Incremental Loading

The `fct_orders` model uses dbt incremental materialization with:

- `order_id` as the unique key.
- `delete+insert` as the incremental strategy.
- `updated_at` as the incremental filter.

This allows updated order records to be processed without rebuilding the entire fact table on every run.

## 7. Data Quality and Referential Integrity

The warehouse applies data quality checks through dbt tests, including:

- Primary and surrogate key uniqueness.
- Required fields not being NULL.
- Accepted values for standardized statuses.
- Referential integrity between dimensions and fact tables.

The source data is preserved, including records with identified anomalies, so that analytical transformations remain traceable.

## 8. Design Notes

The diagrams represent logical relationships established by the ETL and dbt transformations. They do not imply that every relationship is enforced through physical PostgreSQL foreign-key constraints.

The analytical model does not currently contain a separate address dimension. The shipping address identifier is retained in `fct_orders`.

The date keys in the fact tables are derived from the associated order date. They do not represent the payment timestamp.

## 9. Conclusion

The warehouse uses a dimensional design that separates descriptive attributes from measurable business events.

The staging layer preserves the extracted source data, while the analytical layer supports customer, product, category, order, payment and time-based reporting.

This architecture provides a foundation for reliable retail analytics, repeatable transformations and future business intelligence reporting.