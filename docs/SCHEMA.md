# Schema

All SQL lives in `sql/`. Table-creation scripts are safe to rerun (`CREATE TABLE IF NOT EXISTS`).

## Input data

Raw tables mirror the Olist CSV files and are loaded by `batch-predictor load-data` (idempotent: staging table, then `INSERT … ON CONFLICT DO NOTHING`).

| Table | Primary key | Key columns |
|---|---|---|
| `orders` | `order_id` | `customer_id`, `order_status`, `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date` |
| `order_items` | `(order_id, order_item_id)` | `product_id`, `seller_id`, `shipping_limit_date`, `price`, `freight_value` |
| `customers` | `customer_id` | `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state` |
| `sellers` | `seller_id` | `seller_zip_code_prefix`, `seller_city`, `seller_state` |
| `products` | `product_id` | `product_category_name`, `product_photos_qty`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm` |
| `order_payments` | `(order_id, payment_sequential)` | `payment_type`, `payment_installments`, `payment_value` |
| `product_category_translation` | `product_category_name` | `product_category_name_english` |

Other CSV columns are loaded unchanged. Reviews and geolocation files are not loaded (reviews are created after delivery and would leak the outcome).

### Model features (one row per order)

Built by `sql/04_order_features.sql` for orders purchased in a date window `[start, end)`.

| Feature | Source |
|---|---|
| `customer_state` | customers |
| `seller_state`, `main_product_category` | first item of the order |
| `n_items`, `n_sellers`, `total_price`, `total_freight`, `total_weight_g` | order_items / products (aggregated) |
| `payment_type`, `max_installments`, `total_payment_value` | order_payments (aggregated) |
| `est_delivery_days` | estimated delivery date minus purchase timestamp |
| `purchase_hour`, `purchase_dow` | purchase timestamp |
| `same_state` | customer state equals seller state |

The training label `is_late` (delivered after the estimated date) is used only for training and evaluation, never as a model input.

### Input validation rules

| Rule | Outcome |
|---|---|
| Required columns present | Otherwise the run fails with an error listing the missing columns |
| `order_id`, purchase timestamp, `customer_state` not null | Row rejected |
| Numeric columns are numeric | Row rejected |
| `total_price`, `total_freight`, `total_weight_g` ≥ 0 | Row rejected |
| `customer_state` is one of the 27 Brazilian state codes | Row rejected |
| Product category not seen in training | Row accepted; counted and logged as a warning |

## Output: `order_predictions`

| Column | Type | Notes |
|---|---|---|
| `order_id` | TEXT | |
| `model_version` | TEXT | |
| `predicted_proba` | DOUBLE PRECISION | Probability the order is late |
| `predicted_label` | SMALLINT | 1 = predicted late, using the configured threshold |
| `predicted_at` | TIMESTAMPTZ | UTC |
| `run_id` | INTEGER | References `batch_runs.run_id` |

**Primary key `(order_id, model_version)`**: the same order cannot be stored twice for one model version. A new model version writes rows alongside earlier ones.

## Run metadata

### `batch_runs`

| Column | Type | Notes |
|---|---|---|
| `run_id` | SERIAL, primary key | |
| `window_start`, `window_end` | TIMESTAMP | Purchase-date window `[start, end)` |
| `model_version` | TEXT | |
| `status` | TEXT | `running`, `succeeded` or `failed` |
| `rows_read`, `rows_valid`, `rows_rejected`, `rows_written` | INTEGER | |
| `started_at`, `finished_at` | TIMESTAMPTZ | |
| `error_message` | TEXT | Set when `status = 'failed'` |

### `rejected_records`

| Column | Type | Notes |
|---|---|---|
| `run_id` | INTEGER | References `batch_runs.run_id` |
| `order_id` | TEXT | |
| `reason` | TEXT | Which validation rule failed |
| `rejected_at` | TIMESTAMPTZ | |
