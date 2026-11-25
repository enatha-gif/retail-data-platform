\# Source Data Quality Assessment



\## 1. Overview



The source database contains seven tables in the PostgreSQL `shop` schema.



The assessment was conducted using ten Python-driven SQL profiling and investigation tests. The source database was accessed using a read-only connection.



Total source records: 7,565.



\## 2. Source Table Volumes



| Table | Records |

|---|---:|

| categories | 8 |

| customers | 310 |

| addresses | 465 |

| products | 48 |

| orders | 1,500 |

| order\_items | 3,651 |

| payments | 1,583 |

| \*\*Total\*\* | \*\*7,565\*\* |



\## 3. Primary Key Validation



All seven tables passed the primary ID uniqueness checks.



No duplicate primary IDs were identified.



\## 4. Relationship Validation



Seven foreign-key relationships were investigated.



All seven relationships had zero orphan records.



\## 5. Missing Values



| Table | Column | Missing records |

|---|---|---:|

| customers | email | 15 |

| customers | phone | 12 |

| addresses | postal\_code | 465 |

| products | cost\_price | 5 |

| payments | transaction\_ref | 85 |

| payments | paid\_at | 302 |



Missing payment dates were associated with failed and pending payments. All 1,222 successful payments had payment dates.



Missing values will be preserved as NULL in the warehouse.



\## 6. Business Value Validation



The investigation identified:



\- One order with a negative total amount.

\- Five order items with negative quantities.

\- No products with zero or negative selling prices.

\- No negative product cost prices.

\- No invalid discounts below 0% or above 100%.

\- No payments with zero or negative amounts.



The negative quantities and negative order total will be retained in staging and flagged during transformation.



\## 7. Status Standardization



Order statuses contain inconsistent capitalization:



\- COMPLETE

\- completed

\- Completed



These values will be normalized using LOWER(TRIM(status)) in the staging transformation.



Payment statuses and payment methods were also profiled to establish their distinct values.



\## 8. Order Total Reconciliation



Order totals were compared against calculated order-item totals using:



quantity × unit\_price × (1 - discount\_pct / 100)



Results:



| Measure | Result |

|---|---:|

| Total orders | 1,500 |

| Matching orders | 1,493 |

| Mismatching orders | 7 |



All seven mismatching orders had a difference of exactly 1,500.



Further investigation found that successful payment amounts generally matched recorded order totals for completed orders. However, one investigated shipped order had a payment amount of 65,500 against a recorded order total of 66,000.



The source schema does not contain an explicit shipping-fee field. Therefore, the 1,500 difference is classified as an unexplained adjustment and will not be assumed to represent shipping.



\## 9. ETL Treatment Decisions



1\. Preserve source records without modifying the source database.

2\. Use updated\_at for incremental extraction.

3\. Preserve missing values as NULL.

4\. Normalize order statuses in staging.

5\. Preserve anomalous source values for traceability.

6\. Add data-quality flags in analytical models.

7\. Reconcile order totals against order-item calculations.

8\. Make warehouse loads idempotent to prevent duplicate records.



\## 10. Conclusion



The source database has reliable primary identifiers and relationships. However, it contains missing optional values, inconsistent order-status capitalization, negative order-item quantities, and seven order-total discrepancies.



These findings will guide the Python ETL pipeline and dbt transformations.



