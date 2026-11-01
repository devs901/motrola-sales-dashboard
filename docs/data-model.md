# Data model (star schema)

One fact table (`fact_sales`, one row per order line) surrounded by four dimensions.

```
 dim_product ──┐
 dim_region  ──┼──< fact_sales >── dim_date
 dim_channel ──┘
```

## Relationships (Model view → drag the key onto the matching key)

| From (many) | To (one) | Cardinality |
|---|---|---|
| fact_sales[product_id] | dim_product[product_id] | many-to-one |
| fact_sales[region_id]  | dim_region[region_id]   | many-to-one |
| fact_sales[channel_id] | dim_channel[channel_id] | many-to-one |
| fact_sales[order_date] | dim_date[date]          | many-to-one |

All relationships: single direction (dimension → fact), active.

Then select `dim_date` → **Table tools → Mark as date table** → choose `date`.

## Columns

| Table | Key columns |
|---|---|
| fact_sales | order_line_id, order_date, product_id, region_id, channel_id, units, mrp, discount_pct, unit_price, unit_cost, returned (0/1), customer_rating |
| dim_product | product_id, model, variant, series, price_band, launch_date, mrp, unit_cost |
| dim_region | region_id, state, zone, hub_city |
| dim_channel | channel_id, channel, channel_type |
| dim_date | date, year, month_num, month_name, month_start, year_month, quarter, weekday |

## Suggested column tweaks

- `dim_date[month_name]` → **Sort by column** → `month_num`
- `fact_sales[order_date]` → data type **Date**
- `fact_sales[returned]` → keep as whole number (used in a measure)
- Hide the key columns in Report view (right-click → Hide) so users pick from dimension tables.
