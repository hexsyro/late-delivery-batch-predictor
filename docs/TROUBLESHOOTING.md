# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `connection refused` or `could not connect to server` | PostgreSQL is not running, or `DATABASE_URL` points to the wrong host/port | Run `docker compose up -d`, check `docker compose ps`, and compare `.env` with `docker-compose.yml` |
| `password authentication failed` | Password in `.env` differs from the database's | Make the `.env` password match `docker-compose.yml`; if the volume already exists, remove it (`docker compose down -v`) to reinitialise |
| `Missing environment variable: DATABASE_URL` | `.env` missing or not loaded | Copy `.env.example` to `.env`; when running from cron, use absolute paths |
| `relation "orders" does not exist` | Tables not created | Run `sql/01_create_tables.sql` and `sql/02_create_prediction_tables.sql` |
| `model file not found` | No model trained yet, or `model_dir` points elsewhere | Run `batch-predictor train`; check `model_dir` in `config/config.yaml` |
| Warning about scikit-learn version mismatch when loading the model | Environment differs from the one used for training | Reinstall pinned versions (`requirements.lock.txt`) or retrain in the current environment |
| `predict` reports "already processed" | A succeeded run exists for this window and model version | Expected behaviour. Use `--force` only to deliberately overwrite |
| Many rows in `rejected_records` | Source data changed or a validation rule is too strict | Group by `reason`, inspect examples, then fix the data or the rule |
| `predict --next` selects an unexpected window | `batch_runs` has an unexpected last succeeded window | Query `batch_runs` and, if needed, run an explicit `--start/--end` window |
| Scheduled job does nothing | Cron/Task Scheduler cannot find the environment or paths | Check `logs/cron.log`; use absolute paths to the script, virtual environment and repository |
| Integration tests skipped | `TEST_DATABASE_URL` not set | Create the test database and set the variable in `.env` |
