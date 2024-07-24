## Note


## Project Overview
This project involves typical analytical data engineering processes, starting with the ingestion of data from various sources and loading it into the Snowflake data warehouse. Within Snowflake, the data undergoes a series of transformations to prepare it for Business Intelligence (BI) purposes. The BI tool Power BI connects to the data warehouse to generate diverse dashboards and reports.

![Project Overview](./Img/Project_overview.png)

## Data Overview
![Fact and Dimention Tables](./Img/fact_dim_tables.png)

The dataset utilized originates from TPCDS, a well-known dataset designed for database testing, with a specific emphasis on Retail Sales. It encompasses sales records from both websites and catalogs, along with detailed information on inventory levels for each item within every warehouse. Moreover, it incorporates 15 dimensional tables containing valuable information about customers, warehouses, items, and more.

#### The dataset is divided into two parts:
* **RDS:** All tables, except for the inventory tables, are stored in the Postgres DB in AWS RDS. These tables are refreshed every day with the latest sales data, requiring daily ETL processes. 

* **S3 Bucket:** The single Inventory table is stored in a S3 bucket as CSV file. Each day, a new file containing the most recent data is deposited into the S3 bucket. The inventory table typically registers data at the end of each week, leading to one entry per item per warehouse on a weekly basis.

## Snowflake Data Warehouse Requirements
In order to meet the BI requirements, we need to create new tables in the data warehouse. Here are the requirements for the new tables:

1. Combine certain raw tables, for merging various customer-related tables into a single table.
2. As all BI requirements are on a weekly basis, we establish a new fact table weekly, incorporating multiple additional metrics:
* **sum_qty_wk:** The sum of sales_quantity for this week.
* **sum_amt_wk:** The sum of sales_amount for this week.
* **sum_profit_wk:** The sum of net_profit for this week.
* **avg_qty_dy:** The average daily sales_quantity for this week (= sum_qty_wk/7).
* **inv_on_hand_qty_wk:** The item’s inventory on hand at the end of each week in all warehouses (= The inventory on hand at the end of this week).
* **wks_sply:** Weeks of supply, an estimated metric to see how many weeks the inventory can supply the sales (inv_on_hand_qty_wk/sum_qty_wk).
* **low_stock_flg_wk:** Low stock weekly flag. For example, if there is a single day `where (avg_qty_dy > 0 && (avg_qty_dy > inventory_on_hand_qty_wk))` in the week, then mark this week's flag as `True`.

## Tools
* Ingestion Tools
1. Airbyte
2. AWS Lambda Function
* Warehousing Tool
1. Snowflake
* Visualization Tool
1. Power BI

## Diving Into ETL Steps

### 1. Data Ingestion:
We need in this stage to ingest data from multiple sources into snowflake.

| Airbyte | Lambda Function |
|---------| ----------------|
|Ingest data from **`RDS (PostgreSQL)`**, Which Contains 17 tables refreshed daily with the latest sales data. | Ingest data from **`S3 Bucket`** that stores daily CSV file with the latest inventory data. |
<hr>

* **AWS Lambda Function**

I Created an inventory table in Snowflake to hold the CSV inventory data that stored in S3 bucket. I Used the Python script <a href="Lambda_function/ingest_inv_to_snowflake.py">`Lambda_function/ingest_inv_to_snowflake.py`</a> to ingest the inventory data from the S3 bucket into Snowflake. For automation I used AWS CloudWatch to automates the execution of the Lambda function every day at 3:00 AM.

* **Airbyte**

![Airbyte Ingestion Process](./Img/airbyte_ingestion_process.png)

The data in RDS is updated daily at 12:00 AM, And I used Airbyte to ingest data from RDS every day at 3:00 AM to ensure availability of the updated data.

### 2. Data Transformation:
This is a transformation process of the ingested data within the Snowflake data warehouse, divided into three schemas: Raw, Intermediate, and Analytics.

![Database Schemas](./Img/db_with_schemas.png)

#### Schemas Design:
| Raw Schema | Intermediate Schema | Analytics Schema |
|------------| ------------------- | -----------------|
| Contains unaltered data ingested from the sources (RDS and S3). | A staging area where data is cleaned and transformed. | The final, optimized schema for BI and analysis. |

## Intermediate Schema:
The Intermediate schema is designed to transform raw data into a more refined format, suitable for further analysis and reporting. This schema includes two primary tables:

1. `Customer_snapshot`: A snapshot of the `Customer` table from the Raw schema, with a **Slowly Changing Dimension (SDC) Type 2** applied.
2. `Daily_aggregated_sales`: Aggregates daily sales data from multiple tables in the Raw schema.

#### 1. Customer_snapshot Table

The `Customer_snapshot` table is created as a copy of the `Customer` table from the Raw schema. This approach ensures that the original raw data remains untouched, providing a stable basis for further transformations. Additionally, a **Slowly Changing Dimension Type 2 (SCD)** is applied to capture historical changes in customer data.

For the actual SQL script used to create this table and apply SCD Type 2, please refer to the [Customer_snapshot SQL Script](sql_scripts/customer_dimention.sql)

![Customer_snapshot Table](./Img/customer_snapshot_intermediate_Schema.png)

#### 2. Daily_aggregated_sales Table
The `Daily_aggregated_sales` table aggregates daily sales data from multiple raw tables. This table provides essential data for the production schema (Analytics schema), where it is used to build the `Weekly_saled_inventory` table, offering insights into weekly sales performance.

The data is aggregated from various tables in the Raw schema, including `Catalog_sales`, `Web_sales`, and `Date_dim`, To provide comprehensive daily summaries of sales activities.
To feed data into the Analytics schema, where it is used to construct the `Weekly_saled_inventory` table, offering insights into weekly sales performance and supporting business decision-making.

![Daily_aggregated_sales Table](./Img/modeling_intermediate_schema.png)

For the actual SQL script used to create this table, please refer to the [Daily_aggregated_sales SQL Script](sql_scripts/daily_aggregated_sales.sql).

## Analytics Schema (Production schema):
The analytics schema is designed to provide a refined and comprehensive view of the data for analysis and reporting. This schema includes two primary tables:

1. `Customer_dim`: Contains enriched customer data from the `Customer_snapshot` table in the Intermediate schema, along with additional columns from various raw tables.
2. `Weekly_sales_inventory`: Aggregates weekly sales data using the `Daily_aggregated_sales` table from the Intermediate schema and the `Inventory` table from the raw schema.

#### 1. Customer_dim Table
The `Customer_dim` table contains enriched customer data by combining information from the `Customer_snapshot` table in the intermediate schema with additional data from the `Customer_address`, `Customer_demographics`, `Household_demographics`, and `Income_band` tables in the Raw schema. This table provides a comprehensive view of customer details for better analysis and reporting.

For the actual SQL script used to create this table, please refer to the [Customer_dim SQL Script](sql_scripts/customer_dimention.sql).

![Customer_dim Table](./Img/analytics_schema_customer_dim.png)

#### 2. Weekly_sales_inventory Table
The `Weekly_sales_inventory` table aggregates weekly sales data using the `Daily_aggregated_sales` table from the Intermediate schema and inventory data from the `Inventory` table in the Raw schema. This table provides insights into weekly sales performance and inventory levels, to provide a comprehensive view of weekly sales performance and inventory status, and to support inventory management and sales analysis in the analytics layer.

For the actual SQL script used to create this table, please refer to the [Weekly_sales_inventory SQL Script](sql_scripts/weekly_sales_inventory.sql).

![Customer_dim Table](./Img/analytics_weekly_sales_inventory.png)



