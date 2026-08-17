# TODO

## Priority 1 — Data Integrity

- [ ] Run raw-file inventory on the full CA directory.
- [ ] Run raw-file inventory on the full NCA directory.
- [ ] Confirm actual shard counts for each domain.
- [ ] Quantify patients spanning multiple shards.
- [ ] Verify duplicate handling.
- [ ] Verify CA/NCA diagnosis-based cohort definition.

## Priority 2 — Human BP QC

- [ ] Generate CA vs NCA patient counts.
- [ ] Generate BP measurement counts.
- [ ] Plot SBP/DBP distributions.
- [ ] Compare measurement frequency per patient.
- [ ] Compare missingness between cohorts.
- [ ] Compare age/sex distributions.
- [ ] Compare hospitalization duration.

## Priority 3 — Confounders

- [ ] Finalize surgery handling.
- [ ] Create reviewed BP-impacting medication dictionary.
- [ ] Normalize medication ingredient names.
- [ ] Calculate first BP-impacting medication exposure date.
- [ ] Quantify patients removed/censored by medication rule.
- [ ] Investigate ICU/department measurement-frequency differences.

## Priority 4 — Human Dataset Construction

- [ ] Reconstruct hospitalization episodes.
- [ ] Create 7-day windows.
- [ ] Apply minimum-density rule.
- [ ] Create Day/Night aggregation.
- [ ] Add age and sex.
- [ ] Save patient-level train/val/test split.
- [ ] Export reproducible feature dataset.

## Priority 5 — Human Baselines

- [ ] Logistic Regression.
- [ ] Random Forest.
- [ ] XGBoost if environment permits.
- [ ] Report AUROC + balanced accuracy + sensitivity + specificity + F1.
- [ ] Compare against simple demographic-only baseline.
- [ ] Compare against measurement-frequency-only baseline to assess leakage.

## Priority 6 — Human Deep Learning

- [ ] Re-run BiLSTM + Attention.
- [ ] Use patient-level split only.
- [ ] Add early stopping.
- [ ] Add class weighting / balanced sampling if required.
- [ ] Compare with simpler models before accepting DL improvement.

## Priority 7 — Mouse Preprocessing

- [ ] Parse all workbook sheets.
- [ ] Confirm sheet date/year.
- [ ] Confirm measurement-block times.
- [ ] Confirm zero values mean missing/failed measurements.
- [ ] Confirm group-to-label mapping.
- [ ] Confirm CFPAC A1/A2 meaning from protocol.
- [ ] Create `mouse_tidy.csv`.
- [ ] Plot each animal trajectory.
- [ ] Generate animal-level features.

## Priority 8 — Final Mouse Prediction

- [ ] Establish simple CA/NCA baseline.
- [ ] Evaluate animal-level cross-validation.
- [ ] Compare different tumor groups separately.
- [ ] Inspect probability calibration.
- [ ] Generate final per-animal predictions.
- [ ] Save final metrics and confusion matrix.

## Final Deliverables

- [ ] `processed_human_windows.parquet`
- [ ] `human_feature_table.csv`
- [ ] `human_split.json`
- [ ] `mouse_tidy.csv`
- [ ] `mouse_features.csv`
- [ ] `mouse_predictions.csv`
- [ ] `mouse_metrics.json`
