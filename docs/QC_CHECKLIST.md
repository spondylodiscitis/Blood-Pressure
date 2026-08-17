# QC Checklist

Use this checklist whenever raw data or preprocessing code changes.

## Human Raw Data

- [ ] Count all `ca_*_*.csv` and `nca_*_*.csv` shards by domain.
- [ ] Confirm that shard discovery uses glob and not a fixed `range()`.
- [ ] Record total rows before concatenation.
- [ ] Record unique patient count after concatenation.
- [ ] Count patients spanning more than one shard.
- [ ] Count exact duplicate clinical rows.
- [ ] Check missing `연구번호`.
- [ ] Check date range for each domain.
- [ ] Confirm expected columns exist.
- [ ] Confirm CA/NCA labels are consistent with diagnosis rules.

## Vital Signs

- [ ] Count total BP measurements.
- [ ] Calculate missingness for SBP/DBP.
- [ ] Compare raw vs `_클린징` availability.
- [ ] Check implausible / zero values.
- [ ] Plot SBP/DBP distributions.
- [ ] Calculate measurements per patient.
- [ ] Compare measurement frequency between CA and NCA.
- [ ] Compare inpatient duration between CA and NCA.
- [ ] Confirm missingness is not strongly acting as a label proxy.

## Surgery

- [ ] Count patients with surgery.
- [ ] Count BP measurements before surgery.
- [ ] Count BP measurements after surgery.
- [ ] Compare surgery prevalence between CA and NCA.
- [ ] Document the exact surgery censoring rule.

## Medication

- [ ] Count medication shards.
- [ ] Count patients spanning multiple drug shards.
- [ ] Check `성분명` missingness.
- [ ] Check `실시일자` missingness.
- [ ] Normalize ingredient names.
- [ ] Match BP-impacting drug dictionary.
- [ ] Count exposed patients.
- [ ] Document whether censoring starts on the exposure date or after it.
- [ ] Confirm no invented medication administration time is used.

## Window Construction

- [ ] Use 7-day window configuration.
- [ ] Record number of windows before density filtering.
- [ ] Record excluded windows and reason.
- [ ] Verify long admissions can generate multiple windows.
- [ ] Verify all windows preserve patient ID.
- [ ] Confirm day/night boundary settings.
- [ ] Inspect sample patient trajectories manually.

## Split

- [ ] Split by patient, never by row/window.
- [ ] Verify no patient overlap across train/val/test.
- [ ] Compare label distribution across splits.
- [ ] Compare age/sex distribution across splits.
- [ ] Save split IDs for reproducibility.

## Model Evaluation

- [ ] AUROC
- [ ] Balanced accuracy
- [ ] Sensitivity / recall
- [ ] Specificity
- [ ] F1 score
- [ ] Confusion matrix
- [ ] Accuracy
- [ ] Calibration if probability interpretation is required

## Mouse

- [ ] Confirm each worksheet date is parsed correctly.
- [ ] Confirm measurement block/time parsing.
- [ ] Preserve original group names.
- [ ] Confirm `control` mapping.
- [ ] Confirm cancer-group mapping against animal protocol.
- [ ] Confirm meaning of CFPAC A1/A2.
- [ ] Build composite `animal_id`.
- [ ] Confirm no animal ID collision.
- [ ] Treat 0-only measurement rows according to confirmed protocol.
- [ ] Count measurements per animal.
- [ ] Plot each animal trajectory.
- [ ] Compare CA vs NCA distributions.
- [ ] Split/evaluate by animal, never by measurement row.
