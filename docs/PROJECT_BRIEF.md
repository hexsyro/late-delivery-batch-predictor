# Project Brief

## Prediction task and intended use

For every order placed on the marketplace, predict whether it will be **delivered after its estimated delivery date** ("late"). The system outputs a probability and a 0/1 label per order.

Intended use: an operations team reviews the highest-risk orders each week (for example, to check the seller or proactively contact the customer). Predictions support prioritisation; they are not used to make automatic decisions about customers.

## Inputs, outputs and scope

- **Inputs:** order, item, customer, seller, product and payment records stored in PostgreSQL. Only information available **at purchase time** is used (see `SCHEMA.md` for the feature list).
- **Outputs:** one row per order and model version in `order_predictions` (probability, label, `predicted_at`, `run_id`), plus run metadata in `batch_runs` and invalid rows in `rejected_records`.
- **Scope:** weekly batches of orders identified by purchase date; one marketplace; training uses delivered orders only.

## Validation approach

- **Time-based split:** the model trains on orders purchased before `training.train_end_date` (see `config/config.yaml`) and is evaluated on the following month. Data is never shuffled across time, mirroring real use (learn from the past, score the future).
- **Leakage control:** columns known only after purchase are excluded from the features: approval timestamp, carrier hand-over date, delivery date, delivery status, and review data.
- **Input validation at run time:** required columns, null checks, numeric ranges and allowed values (see `SCHEMA.md`).

## Baseline

A `DummyClassifier(strategy="prior")` that predicts the late-delivery base rate for every order. The trained pipeline is only saved if it beats this baseline on the evaluation window.

## Metrics in plain language

- **ROC-AUC:** if you pick one late order and one on-time order at random, the probability that the model gives the late order the higher score. 0.5 is chance; 1.0 is perfect ranking.
- **PR-AUC (average precision):** how well the model ranks late orders ahead of on-time ones when late orders are rare. It is more informative than accuracy for imbalanced data.
- **Recall at a threshold:** of all orders that were actually late, the share the model flags at the chosen probability threshold. Raising the threshold flags fewer orders with higher precision but lower recall.

Accuracy is not used as the headline metric because a model that never predicts "late" would still look accurate.

## Acceptance criteria

1. The trained pipeline beats the baseline on ROC-AUC and PR-AUC on the evaluation window.
2. Running the same batch window twice creates no duplicate rows in `order_predictions`.
3. Invalid input rows are written to `rejected_records` with a reason, and valid rows in the same batch are still predicted.
4. A run that fails part-way leaves no partial predictions and is recorded as `failed` in `batch_runs`.
5. Scheduled execution processes consecutive windows with `predict --next`.
6. Unseen categories and missing numeric values do not crash prediction.
7. Unit and integration tests pass.

## Limitations

See `LIMITATIONS.md`.

## Exclusions

Not included: real-time or streaming prediction, distributed processing, high-availability infrastructure, automated retraining, deep learning, and any claim of guaranteed accuracy.
