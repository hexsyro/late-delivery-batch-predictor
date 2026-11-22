# Operating Guide

## Installation

Requirements: Python 3.10+, Docker (for local PostgreSQL) or a PostgreSQL 14+ server.

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d
```

Download the Olist CSV files into `data/raw/`. Create the tables by running `sql/01_create_tables.sql` and `sql/02_create_prediction_tables.sql` (for example `docker compose exec -T postgres psql -U batch_user -d batch_db < sql/01_create_tables.sql`).

## Configuration

| Setting | Where | Meaning |
|---|---|---|
| `DATABASE_URL` | `.env` | SQLAlchemy URL of the working database |
| `TEST_DATABASE_URL` | `.env` | Separate database used only by integration tests |
| `data_dir`, `model_dir`, `report_dir` | `config/config.yaml` | Input, model and report folders |
| `training.train_end_date` | `config/config.yaml` | Orders purchased before this date are used for training |
| `batches.first_batch_start` | `config/config.yaml` | Start of the first batch window |
| `batches.window_days` | `config/config.yaml` | Length of each batch window |

Secrets stay in `.env`, which is not committed.

## Training

```bash
batch-predictor load-data     # safe to run repeatedly
batch-predictor train
```

`train` reads the training and evaluation windows, fits a baseline and the pipeline, compares them, and saves the pipeline plus a metadata JSON (model version, training window, feature list, metrics, scikit-learn version). The pipeline is not saved if it fails to beat the baseline.

## Running a batch

```bash
batch-predictor predict --start 2018-07-01 --end 2018-07-08   # explicit window [start, end)
batch-predictor predict --next                                # first window after the last succeeded one
```

Each run: loads the saved pipeline (no retraining), reads features, validates rows, predicts, and writes predictions, rejections and run status in a single transaction. The process exits with a non-zero code if the run fails.

## Rerunning a batch safely

- Rerunning the same window with the same model version does nothing new: the run is reported as already processed, and writes use `ON CONFLICT (order_id, model_version) DO NOTHING`.
- A new model version writes its own rows next to the earlier ones.
- `--force` re-processes a window and overwrites existing rows for that model version (`DO UPDATE`). Use it only after fixing a problem with the inputs or configuration.
- If a run fails, nothing from that run is saved. The failure is recorded as `failed` in `batch_runs`; fix the cause and rerun the same window.

## Scheduling

`scripts/run_scheduled_batch.sh` activates the virtual environment, changes to the repository directory and runs `batch-predictor predict --next`, appending output to `logs/cron.log`.

- **Linux/macOS (cron):** `crontab -e`, then add `0 2 * * * /absolute/path/to/scripts/run_scheduled_batch.sh` (every day at 02:00).
- **Windows:** Task Scheduler → Create Basic Task → run a `.bat` file that calls `batch-predictor predict --next`.

Use absolute paths: schedulers run with a minimal environment. The machine must be on at the scheduled time.

## Reading the run summary

```bash
batch-predictor summary --run-id 1
```

The summary (also saved as `reports/run_<id>.json`) shows: run ID, window, model version, status, rows read / valid / rejected / written, rejections by reason, duration, and the error message if the run failed. Detailed events are in `logs/batch.log` (rotating file).

Useful checks in SQL:

```sql
SELECT status, COUNT(*) FROM batch_runs GROUP BY status;
SELECT reason, COUNT(*) FROM rejected_records GROUP BY reason ORDER BY 2 DESC;
SELECT order_id, model_version, COUNT(*) FROM order_predictions
GROUP BY 1, 2 HAVING COUNT(*) > 1;           -- must return no rows
```
