# Limitations and Assumptions

## Data and modelling

- **Historical replay, not live data.** The dataset covers a past period; "new" batches are weekly windows replayed from it. Real traffic would differ in volume, timing and quality.
- **One marketplace, one country.** Patterns (such as state-to-state delivery times) may not transfer elsewhere.
- **Purchase-time features only.** Excluding delivery-stage information avoids leakage but limits how accurate predictions can be.
- **Imbalanced target.** Late deliveries are the minority class; probabilities are better used for ranking and prioritising than as exact likelihoods unless they are calibrated.
- **Estimated delivery date is an input.** If the marketplace changes how it estimates dates, the model's behaviour will change.
- **No guarantee of accuracy.** Metrics describe performance on one evaluation window and may not hold for future periods.

## System

- **Single machine.** The job and scheduler run on one host; scheduled runs happen only while it is on.
- **Model files depend on library versions.** A saved scikit-learn pipeline must be loaded with the same scikit-learn version that created it (recorded in the metadata).
- **No automated retraining or drift monitoring.** Models are retrained manually.
- **Local database.** The default setup uses a single local PostgreSQL container without replication or backups.

## Licensing

The Olist dataset is licensed CC BY-NC-SA 4.0 (non-commercial, share-alike). The data is not redistributed in this repository; check the licence before any commercial use.
