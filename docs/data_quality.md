# Source Data Quality Assessment

## 1. Overview

The source database contains seven tables in the PostgreSQL `shop` schema.

The assessment was conducted using ten Python-driven SQL profiling and investigation tests. The source database was accessed using a read-only connection.

**Total source records: 7,565.**

## 2. Source Table Volumes

| Table | Records |
|---|---:|
| categories | 8 |
| customers | 310 |
| addresses | 465 |
| products | 48 |
| orders | 1,500 |
| order_items | 3,651 |
| payments | 1,583 |
| **Total** | **7,565** |

## 3. Primary Key Validation

All seven tables passed the primary ID uniqueness checks.

No duplicate primary IDs were identified.

## 4. Relationship Validation

Seven foreign-key relationships were investigated.

All seven relationships had zero orphan records.

## 5. Missing Values

| Table | Column | Missing records |
|---|---|---:|
| customers | email | 15 |
| customers | phone | 12 |
| addresses | postal_code | 465 |
| products | cost_price | 5 |
| payments | transaction_ref | 85 |
| payments | paid_at | 302 |

Missing payment dates were associated with failed and pending payments. All 1,222 successful payments had payment dates.

Missing values are preserved as NULL in the warehouse.

## 6. Business Value Validation

The investigation identified:

- One order with a negative total amount.
- Five order items with negative quantities.
- No products with zero or negative selling prices.
- No negative product cost prices.
- No invalid discounts below 0% or above 100%.
- No payments with zero or negative amounts.

The negative quantities and negative order total are retained in staging for traceability and can be flagged during analytical transformations.

## 7. Status Standardization

Order statuses contain inconsistent capitalization:

- COMPLETE
- completed
- Completed

These values are normalized in staging using `LOWER(TRIM(status))`, with `complete` mapped to `completed`.

Payment statuses and payment methods were also profiled to establish their distinct values.

## 8. Order Total Reconciliation

Order totals were compared against calculated order-item totals using:

`quantity × unit_price × (1 - discount_pct / 100)`

Results:

| Measure | Result |
|---|---:|
| Total orders | 1,500 |
| Matching orders | 1,493 |
| Mismatching orders | 7 |

All seven mismatching orders had a difference of exactly 1,500.

Further investigation found that one investigated order had a successful payment amount of 65,500 against a recorded order total of 66,000.

The source schema does not contain an explicit shipping-fee field. Therefore, the 1,500 difference is classified as an unexplained adjustment and is not assumed to represent shipping.

## 9. Future-Dated Records

The investigation identified 15 future-dated order-item records associated with six orders.

These records had timestamps of 13 December 2026, later than the ETL execution date of 27 November 2026.

The records were retained in the source database. The ETL extraction logic was updated to cap extraction at the current source timestamp, preventing future-dated records from advancing incremental watermarks incorrectly.

Historical business analysis queries also exclude future-dated orders.

## 10. ETL Treatment Decisions

1. Preserve source records without modifying the source database.
2. Use `updated_at` for incremental extraction.
3. Preserve missing values as NULL.
4. Normalize order statuses in staging.
5. Preserve anomalous source values for traceability.
6. Identify data-quality issues in analytical transformations.
7. Reconcile order totals against order-item calculations.
8. Make warehouse loads idempotent to prevent duplicate records.
9. Prevent future-dated timestamps from advancing extraction watermarks.

## 11. Conclusion

The source database has reliable primary identifiers and relationships. However, it contains missing optional values, inconsistent order-status capitalization, negative order-item quantities, future-dated records, and seven order-total discrepancies.

These findings informed the Python ETL pipeline, PostgreSQL warehouse design, and dbt transformations. The approach preserves source data while improving consistency and traceability in the analytical warehouse