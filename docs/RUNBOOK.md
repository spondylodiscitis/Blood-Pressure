# Runbook

This document describes the recommended execution order for a new researcher.

---

# 0. Environment

Recommended:

```bash
python >= 3.10
```

Core packages:

```bash
pip install pandas numpy openpyxl pyyaml scikit-learn matplotlib
```

Optional for later deep learning:

```bash
pip install torch
```

---

# 1. Set Data Paths

Edit `config/config.yaml`.

Example:

```yaml
paths:
  ca_dir: /home/ads_lj/visiontask/혈압/data/ca
  nca_dir: /home/ads_lj/visiontask/혈압/data/nca
  mouse_xlsx: /home/ads_lj/visiontask/혈압/data/mouse 혈압 결과.xlsx
```

Do not hard-code paths independently in every script.

---

# 2. Inventory Raw Hospital Files

Run:

```bash
python src/01_inventory.py
```

Check:

- number of shards per domain
- total rows
- unique patient IDs
- patients spanning multiple shards

Review output before moving on.

---

# 3. Merge / Inspect Hospital Domains

Use:

```bash
python src/02_merge_hospital.py
```

Recommended output:

```text
outputs/intermediate/
```

The script should produce one logical table per cohort/domain.

Example:

```text
ca_drug.parquet
ca_vs.parquet
nca_drug.parquet
nca_vs.parquet
```

Do not split by shard after this stage.

---

# 4. Human QC

Run:

```bash
python src/03_qc_human.py
```

Review:

- cohort size
- BP availability
- measurement frequency
- medication exposure
- surgery counts
- age/sex imbalance

Do not proceed if there is patient leakage or major schema mismatch.

---

# 5. Build Human Windows

Run:

```bash
python src/04_build_windows.py
```

Expected design:

```text
7-day windows
+
Day/Night aggregation
+
age
+
sex
```

Save exclusion logs.

---

# 6. Train Human Baseline

Run:

```bash
python src/05_train_baseline.py
```

Do not rely on accuracy alone.

At minimum inspect:

```text
AUROC
Balanced accuracy
Sensitivity
Specificity
F1
Confusion matrix
```

Also compare:
- full model
- age/sex only
- measurement-frequency only

This helps detect clinical-workflow leakage.

---

# 7. Parse Mouse Workbook

Run:

```bash
python src/06_preprocess_mouse.py
```

Expected outputs:

```text
outputs/mouse_tidy.csv
outputs/mouse_features.csv
```

Before modeling:
- inspect every group
- inspect animal IDs
- plot trajectories
- confirm zero handling

---

# 8. Train Mouse Baseline

Run:

```bash
python src/07_train_mouse.py
```

Recommended first model:

```text
Logistic Regression
```

Then:

```text
Random Forest
```

Because mouse N is small, avoid using a large neural network as the first model.

---

# 9. Final Output

Each animal should have:

```text
animal_id
original_group
true_label
predicted_probability
predicted_label
```

Save:

```text
outputs/mouse_predictions.csv
outputs/mouse_metrics.json
```

---

# 10. Before Reporting Results

Confirm:

1. no patient leakage
2. no mouse leakage
3. group mapping confirmed
4. confounder rules documented
5. model metric set complete
6. commit hash recorded
7. config archived with result
