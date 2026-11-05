# Data model

Use a **star schema**. `fact_sales` is the central fact table; the four dimensions filter it.

## Relationships

Create these active, single-direction, one-to-many relationships:

| Dimension (one side) | Fact (many side) | Cardinality |
|---|---|---|
| `dim_product[product_id]` | `fact_sales[product_id]` | 1:* |
| `dim_region[region_id]` | `fact_sales[region_id]` | 1:* |
| `dim_channel[channel_id]` | `fact_sales[channel_id]` | 1:* |
| `dim_date[date]` | `fact_sales[order_date]` | 1:* |

Set cross-filter direction to **Single** (dimension → fact). Mark `dim_date` as the date table using `dim_date[date]`.

## Tables

- `fact_sales`: one row per order line; includes date and dimension keys, units, MRP, discount, selling price, unit cost, return flag and optional customer rating.
- `dim_product`: model, series, RAM/storage variant, price band, launch date, MRP and unit cost.
- `dim_region`: state, zone and hub city.
- `dim_channel`: sales channel and channel type.
- `dim_date`: continuous daily calendar from 1 Jan 2025 to 31 Oct 2026.

## Power Query data types

- Dates: `fact_sales[order_date]`, `dim_product[launch_date]`, `dim_date[date]`, `dim_date[month_start]` → Date.
- Whole number: IDs, `units`, `returned`, RAM/storage, year/month/weekday numbers.
- Decimal/fixed decimal: MRP, unit price, unit cost, discount percentage, customer rating.

## Sorting

Select `dim_date[month_name]` and choose **Sort by column → month_num**.
Use `dim_date[year_month]` for chronological month axes.
